"""
ScoutAI — Module 5: Deterministic Match Scoring Engine
Computes skill, experience, and semantic scores using weighted formula.
"""

import logging
from backend.config import MATCH_WEIGHT_SKILL, MATCH_WEIGHT_EXPERIENCE, MATCH_WEIGHT_SEMANTIC

logger = logging.getLogger(__name__)


def score_candidate(
    candidate: dict,
    jd_parsed: dict,
    semantic_score: float = 0.0,
) -> dict:
    """
    Compute deterministic match score for a single candidate.

    Match = 0.5 * Skill + 0.3 * Experience + 0.2 * Semantic

    Returns dict with individual scores and final match_score.
    """
    skill_score = _compute_skill_score(candidate, jd_parsed)
    exp_score = _compute_experience_score(candidate, jd_parsed)
    sem_score = min(semantic_score * 100, 100.0)  # normalise to 0-100

    match_score = (
        MATCH_WEIGHT_SKILL * skill_score
        + MATCH_WEIGHT_EXPERIENCE * exp_score
        + MATCH_WEIGHT_SEMANTIC * sem_score
    )

    result = {
        "skill_score": round(skill_score, 2),
        "experience_score": round(exp_score, 2),
        "semantic_score": round(sem_score, 2),
        "match_score": round(match_score, 2),
        "matched_skills": _get_matched_skills(candidate, jd_parsed),
        "missing_skills": _get_missing_skills(candidate, jd_parsed),
    }

    logger.debug(f"Scored {candidate.get('name', '?')}: "
                 f"skill={skill_score:.1f} exp={exp_score:.1f} "
                 f"sem={sem_score:.1f} → match={match_score:.1f}")
    return result


def score_candidates(
    candidates: list[dict],
    jd_parsed: dict,
    retrieval_results: list[dict],
) -> list[dict]:
    """Score a batch of candidates, using retrieval vector scores as semantic scores."""
    vector_map = {r["candidate_id"]: r["vector_score"] for r in retrieval_results}

    scored = []
    for candidate in candidates:
        cid = candidate["id"]
        semantic = vector_map.get(cid, 0.0)
        scores = score_candidate(candidate, jd_parsed, semantic)
        scored.append({
            "candidate_id": cid,
            "name": candidate["name"],
            **scores,
        })

    # Sort by match_score descending
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    logger.info(f"Scored {len(scored)} candidates")
    return scored


def _compute_skill_score(candidate: dict, jd_parsed: dict) -> float:
    """
    Skill Score = |JD_skills ∩ Candidate_skills| / |JD_skills| × 100
    With temporal weighting: recent work experience skills get 1.2× boost.
    """
    jd_skills = set(s.lower() for s in jd_parsed.get("skills_must_have", []))
    if not jd_skills:
        return 50.0  # No skills specified → neutral score

    candidate_skills = set(s.lower() for s in candidate.get("skills", []))

    # Check for skills in recent projects/work for temporal boost
    recent_text = ""
    work_exp = candidate.get("work_experience", [])
    if work_exp:
        recent_text = (work_exp[0].get("role", "") + " " +
                       work_exp[0].get("company", "")).lower()

    matched = jd_skills & candidate_skills
    base_score = (len(matched) / len(jd_skills)) * 100

    # Temporal boost: if matched skills appear in recent role context
    boost = 0.0
    for skill in matched:
        if skill in recent_text:
            boost += 2.0  # small boost per recent skill

    return min(base_score + boost, 100.0)


def _compute_experience_score(candidate: dict, jd_parsed: dict) -> float:
    """
    Experience Score = min(candidate_years / required_years, 1.0) × 100
    Bonus for exceeding requirements (up to 10 extra points).
    """
    required = jd_parsed.get("experience_required", 0)
    if required <= 0:
        return 75.0  # No requirement → decent default

    actual = candidate.get("experience_years", 0)
    base = min(actual / required, 1.0) * 100

    # Bonus for exceeding (diminishing returns)
    if actual > required:
        excess = actual - required
        bonus = min(excess * 2.5, 10.0)
        base = min(base + bonus, 100.0)

    return base


def _get_matched_skills(candidate: dict, jd_parsed: dict) -> list[str]:
    """Get skills that match between candidate and JD."""
    jd_skills = set(s.lower() for s in
                    jd_parsed.get("skills_must_have", []) +
                    jd_parsed.get("skills_nice_to_have", []))
    candidate_skills = candidate.get("skills", [])
    return [s for s in candidate_skills if s.lower() in jd_skills]


def _get_missing_skills(candidate: dict, jd_parsed: dict) -> list[str]:
    """Get JD must-have skills that candidate is missing."""
    candidate_skills = set(s.lower() for s in candidate.get("skills", []))
    must_have = jd_parsed.get("skills_must_have", [])
    return [s for s in must_have if s.lower() not in candidate_skills]
