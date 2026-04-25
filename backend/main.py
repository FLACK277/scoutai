"""
ScoutAI — FastAPI Application
Main entry point with all API endpoints for the recruitment engine.
"""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.config import FINAL_TOP_K, BASE_DIR
from backend.llm_client import llm
from backend.modules.candidate_db import candidate_db
from backend.modules.jd_parser import parse_jd
from backend.modules.retrieval import hybrid_retrieve
from backend.modules.scoring import score_candidates
from backend.modules.propensity import compute_propensity_batch
from backend.modules.explainability import explain_candidates
from backend.modules.engagement import engage_candidates
from backend.modules.ranking import compute_final_ranking
import os

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scoutai")


# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ScoutAI starting up...")
    candidate_db.load()
    logger.info("✅ ScoutAI ready!")
    yield
    logger.info("ScoutAI shutting down.")


# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScoutAI",
    description="Agentic Hybrid-RAG Recruitment Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_dir = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# ─── In-memory session state ──────────────────────────────────────────────────
session: dict = {}


# ─── Request Models ───────────────────────────────────────────────────────────
class JDRequest(BaseModel):
    jd_text: str


class PipelineRequest(BaseModel):
    jd_text: str
    top_k: int = FINAL_TOP_K
    anonymize: bool = False


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ScoutAI API is running. Frontend not found."}


@app.get("/health")
async def health_check():
    groq_ok = llm.refresh_status()
    return {
        "server": "ok",
        "groq": groq_ok,
        "model": llm.model,
        "mode": "llm" if groq_ok else "fallback",
        "candidates_loaded": len(candidate_db.candidates),
    }


@app.post("/parse-jd")
async def api_parse_jd(req: JDRequest):
    if not req.jd_text.strip():
        raise HTTPException(400, "JD text cannot be empty")
    parsed = await parse_jd(req.jd_text)
    session["jd_parsed"] = parsed
    session["jd_text"] = req.jd_text
    return {"status": "ok", "parsed_jd": parsed}


@app.post("/get-candidates")
async def api_get_candidates():
    jd = session.get("jd_parsed")
    if not jd:
        raise HTTPException(400, "Parse a JD first via /parse-jd")
    results = hybrid_retrieve(jd)
    session["retrieval_results"] = results
    cids = [r["candidate_id"] for r in results]
    candidates = candidate_db.get_by_ids(cids)
    return {
        "status": "ok",
        "count": len(results),
        "retrieval": results,
        "candidates": [{"id": c["id"], "name": c["name"],
                         "skills": c["skills"],
                         "experience_years": c["experience_years"],
                         "current_company": c["current_company"]}
                        for c in candidates],
    }


@app.post("/score-candidates")
async def api_score_candidates():
    jd = session.get("jd_parsed")
    ret = session.get("retrieval_results")
    if not jd or not ret:
        raise HTTPException(400, "Run /get-candidates first")
    cids = [r["candidate_id"] for r in ret]
    candidates = candidate_db.get_by_ids(cids)
    scored = score_candidates(candidates, jd, ret)
    session["scored_results"] = scored
    session["shortlisted_candidates"] = candidates
    return {"status": "ok", "scored": scored}


@app.post("/engage")
async def api_engage():
    jd = session.get("jd_parsed")
    scored = session.get("scored_results")
    candidates = session.get("shortlisted_candidates")
    if not jd or not scored or not candidates:
        raise HTTPException(400, "Run /score-candidates first")
    prop = compute_propensity_batch(candidates)
    eng = await engage_candidates(candidates, jd, scored, prop)
    session["propensity_results"] = prop
    session["engagement_results"] = eng
    return {"status": "ok", "engagement": eng}


@app.get("/ranked-results")
async def api_ranked_results():
    if "ranked" not in session:
        raise HTTPException(400, "Run full pipeline first")
    return {"status": "ok", "ranked": session["ranked"]}


@app.post("/pipeline")
async def api_full_pipeline(req: PipelineRequest):
    """Full pipeline: JD text in → ranked shortlist out."""
    start = time.time()
    mode = "llm" if llm.available else "fallback"
    logger.info(f"━━━ Pipeline started (mode={mode}) ━━━")

    # Step 1: Parse JD
    logger.info("Step 1/6: Parsing JD...")
    jd_parsed = await parse_jd(req.jd_text)

    # Step 2: Retrieve candidates
    logger.info("Step 2/6: Retrieving candidates...")
    retrieval = hybrid_retrieve(jd_parsed, req.top_k)
    cids = [r["candidate_id"] for r in retrieval]
    candidates = candidate_db.get_by_ids(cids)

    # Step 3: Score candidates
    logger.info("Step 3/6: Scoring candidates...")
    scored = score_candidates(candidates, jd_parsed, retrieval)

    # Step 4: Propensity
    logger.info("Step 4/6: Computing propensity...")
    propensity = compute_propensity_batch(candidates)

    # Step 5: Explainability + Engagement
    logger.info("Step 5/6: Generating explanations & engagement...")
    explanations = await explain_candidates(candidates, jd_parsed, scored)
    engagement = await engage_candidates(candidates, jd_parsed, scored, propensity)

    # Step 6: Final ranking
    logger.info("Step 6/6: Computing final ranking...")
    ranked = compute_final_ranking(scored, propensity, engagement, explanations, candidates)

    # Anonymize if requested
    if req.anonymize:
        for i, r in enumerate(ranked):
            r["name"] = f"Candidate {chr(65 + i)}"

    elapsed = round(time.time() - start, 2)
    logger.info(f"━━━ Pipeline complete in {elapsed}s ━━━")

    session["ranked"] = ranked
    session["jd_parsed"] = jd_parsed

    return {
        "status": "ok",
        "mode": mode,
        "elapsed_seconds": elapsed,
        "jd_parsed": jd_parsed,
        "total_candidates": len(candidate_db.candidates),
        "shortlisted": len(ranked),
        "ranked": ranked,
    }
