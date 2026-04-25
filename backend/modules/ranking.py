"""
ScoutAI — Module 9: Final Ranking Engine
Combines match, propensity, and interest scores into a final ranked list.
"""

import logging
from backend.config import FINAL_WEIGHT_MATCH, FINAL_WEIGHT_PROPENSITY, FINAL_WEIGHT_INTEREST

logger = logging.getLogger(__name__)


def compute_final_ranking(
    scored_results: list[dict],
    propensity_results: list[dict],
    engagement_results: list[dict],
    explanation_results: list[dict],
    candidates: list[dict],
) -> list[dict]:
    """
    Final Score = 0.6 * Match + 0.2 * Propensity + 0.2 * Interest
    Returns fully enriched ranked list.
    """
    prop_map = {p["candidate_id"]: p for p in propensity_results}
    eng_map = {e["candidate_id"]: e for e in engagement_results}
    exp_map = {e["candidate_id"]: e for e in explanation_results}
    cand_map = {c["id"]: c for c in candidates}

    ranked = []
    for s in scored_results:
        cid = s["candidate_id"]
        match_score = s.get("match_score", 0)
        prop = prop_map.get(cid, {})
        eng = eng_map.get(cid, {})
        exp = exp_map.get(cid, {})
        cand = cand_map.get(cid, {})

        propensity_score = prop.get("propensity_score", 50)
        interest_score = eng.get("interest_score", 50)

        final_score = (
            FINAL_WEIGHT_MATCH * match_score
            + FINAL_WEIGHT_PROPENSITY * propensity_score
            + FINAL_WEIGHT_INTEREST * interest_score
        )

        ranked.append({
            "rank": 0,  # set after sorting
            "candidate_id": cid,
            "name": s.get("name", cand.get("name", "Unknown")),
            "current_company": cand.get("current_company", ""),
            "experience_years": cand.get("experience_years", 0),
            "skills": cand.get("skills", []),
            # Scores
            "final_score": round(final_score, 2),
            "match_score": round(match_score, 2),
            "skill_score": s.get("skill_score", 0),
            "experience_score": s.get("experience_score", 0),
            "semantic_score": s.get("semantic_score", 0),
            "propensity_score": round(propensity_score, 2),
            "propensity_label": prop.get("propensity_label", "Unknown"),
            "propensity_reason": prop.get("propensity_reason", ""),
            "months_at_job": prop.get("months_at_job", 0),
            "interest_score": round(interest_score, 2),
            "interest_level": eng.get("interest_level", "Unknown"),
            # Details
            "matched_skills": s.get("matched_skills", []),
            "missing_skills": s.get("missing_skills", []),
            "strengths": exp.get("strengths", []),
            "resume_evidence": exp.get("resume_evidence", []),
            "explanation_summary": exp.get("summary", ""),
            "outreach_message": eng.get("outreach_message", ""),
            "candidate_response": eng.get("candidate_response", ""),
            # Meta
            "bias_note": "Scores are algorithm-generated. Human review recommended before final decisions.",
        })

    # Sort by final_score descending
    ranked.sort(key=lambda x: x["final_score"], reverse=True)

    # Assign ranks
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    logger.info(f"Final ranking computed for {len(ranked)} candidates")
    if ranked:
        logger.info(f"Top candidate: {ranked[0]['name']} "
                     f"(final_score={ranked[0]['final_score']})")

    return ranked
