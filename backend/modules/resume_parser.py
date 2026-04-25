"""
ScoutAI — Module 2: Resume Parser
Parses raw resume text into structured JSON using Mistral (with regex fallback).
"""

import re
import logging
from backend.llm_client import llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a precise resume parser. Extract ONLY information explicitly "
    "stated in the resume text. Return valid JSON only. Do not infer or "
    "hallucinate. Do not wrap the JSON in markdown code fences."
)

USER_PROMPT_TEMPLATE = """Extract structured data from this resume. Return valid JSON with these exact keys:
- "name" (string): candidate's full name
- "skills" (array of strings): technical skills mentioned
- "experience_years" (number): total years of experience
- "work_experience" (array of objects with keys: "company", "role", "duration")
- "projects" (array of strings): notable projects or achievements

Resume:
{resume_text}
"""


async def parse_resume(resume_text: str) -> dict:
    """
    Parse raw resume text into structured data.
    Primary: Ollama Mistral. Fallback: regex extraction.
    """
    try:
        if llm.available:
            logger.info("Parsing resume via Mistral...")
            result = await llm.generate_json(
                prompt=USER_PROMPT_TEMPLATE.format(resume_text=resume_text),
                system=SYSTEM_PROMPT,
            )
            parsed = _normalise(result)
            logger.info(f"Resume parsed via LLM: name='{parsed['name']}', "
                        f"{len(parsed['skills'])} skills")
            return parsed
    except Exception as e:
        logger.warning(f"LLM resume parsing failed, falling back: {e}")

    logger.info("Parsing resume via fallback (regex)...")
    return _fallback_parse(resume_text)


def _normalise(data: dict) -> dict:
    """Ensure all expected keys exist with correct types."""
    return {
        "name": str(data.get("name", "Unknown")),
        "skills": list(data.get("skills", [])),
        "experience_years": _safe_int(data.get("experience_years", 0)),
        "work_experience": list(data.get("work_experience", [])),
        "projects": list(data.get("projects", [])),
    }


def _safe_int(val) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _fallback_parse(resume_text: str) -> dict:
    """Regex-based resume parser (no LLM needed)."""
    # ── Name: first line or first capitalised phrase ──
    name = "Unknown"
    first_line = resume_text.strip().split("\n")[0].strip()
    name_match = re.match(r"^([A-Z][a-z]+ [A-Z][a-z]+)", first_line)
    if name_match:
        name = name_match.group(1)
    elif "—" in first_line:
        name = first_line.split("—")[0].strip()

    # ── Experience years ──
    exp_years = 0
    exp_match = re.search(r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience)?",
                          resume_text, re.IGNORECASE)
    if exp_match:
        exp_years = int(exp_match.group(1))

    # ── Skills: look for known tech keywords ──
    from backend.modules.jd_parser import KNOWN_SKILLS
    text_lower = resume_text.lower()
    found_skills = [s for s in KNOWN_SKILLS if s.lower() in text_lower]

    # ── Projects: sentences with action verbs ──
    projects = []
    sentences = re.split(r'[\.!]', resume_text)
    action_verbs = ["built", "designed", "developed", "created", "led",
                    "architected", "implemented", "optimized", "reduced"]
    for sent in sentences:
        sent = sent.strip()
        if any(v in sent.lower() for v in action_verbs) and len(sent) > 20:
            projects.append(sent)

    return {
        "name": name,
        "skills": found_skills,
        "experience_years": exp_years,
        "work_experience": [],
        "projects": projects[:5],
    }
