"""
ScoutAI — Module 4: Hybrid RAG Retrieval Engine
Combines FAISS vector search with keyword skill-overlap filtering via RRF fusion.
"""

import logging
from backend.config import FAISS_TOP_K, KEYWORD_MIN_OVERLAP, FINAL_TOP_K
from backend.embeddings import embedding_manager
from backend.modules.candidate_db import candidate_db

logger = logging.getLogger(__name__)


def hybrid_retrieve(jd_parsed: dict, top_k: int | None = None) -> list[dict]:
    """
    Hybrid retrieval: FAISS vector search + keyword skill-overlap, fused via RRF.
    Returns list of {candidate_id, vector_score, keyword_score, rrf_score}.
    """
    top_k = top_k or FINAL_TOP_K
    jd_skills = set(s.lower() for s in jd_parsed.get("skills_must_have", [])
                    + jd_parsed.get("skills_nice_to_have", []))

    # ── Build a text query from the JD for vector search ──
    query_text = (
        f"{jd_parsed.get('role', '')} "
        f"{' '.join(jd_parsed.get('skills_must_have', []))} "
        f"{' '.join(jd_parsed.get('skills_nice_to_have', []))}"
    )

    # ── Vector path: FAISS cosine similarity ──
    query_vec = embedding_manager.encode(query_text)
    vector_results = embedding_manager.search(query_vec, FAISS_TOP_K)
    # vector_results is list of (candidate_id, similarity_score)

    # ── Keyword path: skill overlap filtering ──
    keyword_results = []
    for candidate in candidate_db.get_all():
        candidate_skills = set(s.lower() for s in candidate.get("skills", []))
        overlap = len(jd_skills & candidate_skills)
        if overlap >= KEYWORD_MIN_OVERLAP:
            keyword_results.append((candidate["id"], overlap))

    # Sort keyword results by overlap count descending
    keyword_results.sort(key=lambda x: x[1], reverse=True)

    # ── RRF Fusion ──
    rrf_scores = _reciprocal_rank_fusion(vector_results, keyword_results)

    # Sort by RRF score and take top_k
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # Build result objects
    vector_map = dict(vector_results)
    keyword_map = dict(keyword_results)

    results = []
    for cid, rrf_score in fused:
        results.append({
            "candidate_id": cid,
            "vector_score": round(vector_map.get(cid, 0.0), 4),
            "keyword_overlap": keyword_map.get(cid, 0),
            "rrf_score": round(rrf_score, 4),
        })

    logger.info(f"Hybrid retrieval: {len(vector_results)} vector hits, "
                f"{len(keyword_results)} keyword hits → {len(results)} fused results")
    return results


def _reciprocal_rank_fusion(
    vector_ranked: list[tuple[int, float]],
    keyword_ranked: list[tuple[int, float]],
    k: int = 60,
) -> dict[int, float]:
    """
    Reciprocal Rank Fusion: combines two ranked lists.
    RRF(d) = Σ 1 / (k + rank_i(d))  for each ranking i.
    """
    scores: dict[int, float] = {}

    for rank, (cid, _) in enumerate(vector_ranked, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    for rank, (cid, _) in enumerate(keyword_ranked, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    return scores
