"""
ScoutAI — Module 8: Engagement Agent
Generates personalised outreach and simulates candidate responses via Mistral.
"""

import logging
import random
from backend.llm_client import llm

logger = logging.getLogger(__name__)

OUTREACH_SYSTEM = "You are a professional tech recruiter. Write warm, concise outreach messages."

OUTREACH_PROMPT = """Write a brief outreach to {name} for the {role} position.
Skills: {skills}. Current: {current_role} at {current_company}.
Under 100 words. No markdown."""

RESPONSE_SYSTEM = "You are simulating a candidate's response. Return valid JSON only."

RESPONSE_PROMPT = """You are {name}, {exp}-year dev at {company} for {months} months.
Propensity: {propensity}/100. Respond to recruiter for {role}.
Return JSON: {{"response":"1-2 sentences","interest_level":"Interested|Neutral|Not Interested"}}"""


async def engage_candidate(candidate, jd_parsed, scores, propensity):
    role = jd_parsed.get("role", "Software Engineer")
    matched = scores.get("matched_skills", candidate.get("skills", [])[:3])
    top_skills = ", ".join(matched[:4])
    outreach = await _gen_outreach(candidate, role, top_skills)
    resp = await _sim_response(candidate, role, propensity)
    level = resp.get("interest_level", "Neutral")
    return {
        "outreach_message": outreach,
        "candidate_response": resp.get("response", ""),
        "interest_level": level,
        "interest_score": {"Interested": 85.0, "Neutral": 50.0, "Not Interested": 15.0}.get(level, 50.0),
    }


async def engage_candidates(candidates, jd_parsed, scored_results, propensity_results):
    sm = {s["candidate_id"]: s for s in scored_results}
    pm = {p["candidate_id"]: p for p in propensity_results}
    results = []
    for c in candidates:
        cid = c["id"]
        eng = await engage_candidate(c, jd_parsed, sm.get(cid, {}), pm.get(cid, {}))
        results.append({"candidate_id": cid, "name": c["name"], **eng})
    return results


async def _gen_outreach(candidate, role, top_skills):
    we = candidate.get("work_experience", [])
    cr = we[0]["role"] if we else "Developer"
    cc = candidate.get("current_company", "their company")
    try:
        if llm.available:
            return await llm.generate(
                prompt=OUTREACH_PROMPT.format(name=candidate["name"], role=role,
                    skills=top_skills, current_role=cr, current_company=cc),
                system=OUTREACH_SYSTEM)
    except Exception as e:
        logger.warning(f"LLM outreach failed: {e}")
    return (f"Hi {candidate['name']},\n\nI was impressed by your work as {cr} at {cc}. "
            f"We have an exciting {role} opportunity matching your expertise in {top_skills}. "
            f"Would you be open to a quick chat?\n\nBest,\nScoutAI Team")


async def _sim_response(candidate, role, propensity):
    months = propensity.get("months_at_job", 12)
    ps = propensity.get("propensity_score", 50)
    try:
        if llm.available:
            return await llm.generate_json(
                prompt=RESPONSE_PROMPT.format(name=candidate["name"],
                    exp=candidate.get("experience_years", 3),
                    company=candidate.get("current_company", "my company"),
                    months=months, propensity=int(ps), role=role),
                system=RESPONSE_SYSTEM)
    except Exception as e:
        logger.warning(f"LLM response sim failed: {e}")
    if ps >= 70:
        return {"response": f"Thanks! The {role} role sounds great. Let's connect.", "interest_level": "Interested"}
    elif ps >= 45:
        return {"response": f"Appreciate the outreach. I'm open to hearing more about the {role} position.", "interest_level": "Neutral"}
    else:
        return {"response": "Thank you, but I'm happy in my current role right now.", "interest_level": "Not Interested"}
