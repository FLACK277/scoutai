"""
ScoutAI — Module 7: Explainability Engine
Generates per-candidate explanations using Groq/Mixtral (with deterministic fallback).
"""

import logging
from backend.llm_client import llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an explainable AI recruitment assistant. Given the JD requirements "
    "and candidate resume, generate a structured explanation. Be concise, "
    "evidence-based, and never fabricate information. Return valid JSON only. "
    "Do not wrap the JSON in markdown code fences."
)

USER_PROMPT_TEMPLATE = """Analyse this candidate against the job requirements. Return JSON with these exact keys:
- "strengths" (array of strings): matched skills and relevant experience, with evidence from resume
- "missing_skills" (array of strings): JD skills the candidate lacks
- "resume_evidence" (array of strings): exact phrases from the resume supporting the match
- "summary" (string): 2-sentence overall assessment

JD Requirements:
Role: {role}
Must-have skills: {must_have}
Nice-to-have skills: {nice_to_have}
Experience required: {exp_required} years

Candidate Resume:
{resume_text}
"""


async def explain_candidate(candidate: dict, jd_parsed: dict, scores: dict) -> dict:
    """
    Generate an explanation for why a candidate matches (or doesn't match) a JD.
    Primary: Groq Mixtral. Fallback: deterministic set-intersection.
    """
    try:
        if llm.available:
            logger.info(f"Generating explanation for {candidate['name']} via Groq/Mixtral...")
            prompt = USER_PROMPT_TEMPLATE.format(
                role=jd_parsed.get("role", ""),
                must_have=", ".join(jd_parsed.get("skills_must_have", [])),
                nice_to_have=", ".join(jd_parsed.get("skills_nice_to_have", [])),
                exp_required=jd_parsed.get("experience_required", 0),
                resume_text=candidate.get("raw_resume_text", ""),
            )
            result = await llm.generate_json(prompt=prompt, system=SYSTEM_PROMPT)
            return _normalise(result)
    except Exception as e:
        logger.warning(f"LLM explanation failed for {candidate['name']}, "
                       f"falling back: {e}")

    return _fallback_explain(candidate, jd_parsed, scores)


async def explain_candidates(
    candidates: list[dict],
    jd_parsed: dict,
    scored_results: list[dict],
) -> list[dict]:
    """Generate explanations for a list of candidates."""
    score_map = {s["candidate_id"]: s for s in scored_results}
    results = []

    for candidate in candidates:
        cid = candidate["id"]
        scores = score_map.get(cid, {})
        explanation = await explain_candidate(candidate, jd_parsed, scores)
        results.append({
            "candidate_id": cid,
            "name": candidate["name"],
            **explanation,
        })

    return results


def _normalise(data: dict) -> dict:
    """Ensure all expected keys exist."""
    return {
        "strengths": list(data.get("strengths", [])),
        "missing_skills": list(data.get("missing_skills", [])),
        "resume_evidence": list(data.get("resume_evidence", [])),
        "summary": str(data.get("summary", "No summary available.")),
    }


def _fallback_explain(candidate: dict, jd_parsed: dict, scores: dict) -> dict:
    """Deterministic set-intersection explainability (no LLM)."""
    candidate_skills = set(s.lower() for s in candidate.get("skills", []))
    jd_must = jd_parsed.get("skills_must_have", [])
    jd_nice = jd_parsed.get("skills_nice_to_have", [])
    all_jd = set(s.lower() for s in jd_must + jd_nice)

    # Strengths
    matched = [s for s in candidate.get("skills", []) if s.lower() in all_jd]
    strengths = []
    for skill in matched:
        strengths.append(f"Has {skill} experience")

    exp = candidate.get("experience_years", 0)
    req = jd_parsed.get("experience_required", 0)
    if exp >= req and req > 0:
        strengths.append(f"{exp} years of experience meets the {req}-year requirement")

    # Missing skills
    missing = [s for s in jd_must if s.lower() not in candidate_skills]

    # Resume evidence: extract sentences containing matched skills
    resume_text = candidate.get("raw_resume_text", "")
    evidence = []
    sentences = resume_text.replace(". ", ".\n").split("\n")
    for skill in matched[:3]:
        for sent in sentences:
            if skill.lower() in sent.lower() and len(sent.strip()) > 10:
                evidence.append(sent.strip())
                break

    # Summary
    match_pct = scores.get("match_score", 0)
    if match_pct >= 70:
        quality = "strong"
    elif match_pct >= 50:
        quality = "moderate"
    else:
        quality = "partial"

    summary = (
        f"{candidate['name']} is a {quality} match with "
        f"{len(matched)}/{len(set(jd_must))} must-have skills. "
        f"{'They exceed' if exp > req else 'They meet' if exp >= req else 'They fall short of'} "
        f"the {req}-year experience requirement with {exp} years."
    )

    return {
        "strengths": strengths,
        "missing_skills": missing,
        "resume_evidence": evidence[:5],
        "summary": summary,
    }
