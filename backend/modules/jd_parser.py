"""
ScoutAI — Module 1: Job Description Parser
Parses raw JD text into structured JSON using Groq/Mixtral (with regex fallback).
"""

import re
import logging
from backend.llm_client import llm

logger = logging.getLogger(__name__)

# ─── Common skill keywords for regex fallback ──────────────────────────────────
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "React", "Angular", "Vue.js", "Next.js", "Node.js", "Django", "Flask",
    "FastAPI", "Spring Boot", "Express.js", "Rails",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Snowflake",
    "Oracle", "SQL", "DynamoDB", "Cassandra",
    "Docker", "Kubernetes", "Terraform", "AWS", "GCP", "Azure", "CI/CD",
    "Jenkins", "Linux", "Nginx",
    "TensorFlow", "PyTorch", "scikit-learn", "NLP", "Computer Vision",
    "LLMs", "RAG", "FAISS", "Hugging Face", "MLflow", "BERT", "Transformers",
    "Kafka", "RabbitMQ", "gRPC", "REST APIs", "GraphQL", "Microservices",
    "Celery", "Airflow", "Apache Spark", "dbt",
    "Git", "Figma", "Storybook", "Tailwind CSS", "WebGL",
    "Pandas", "NumPy", "Tableau", "A/B Testing", "Statistics",
    "React Native", "Firebase", "Redux", "OpenCV", "CUDA", "Edge AI",
    "Prometheus", "Networking", "Performance", "Systems Programming",
]

SYSTEM_PROMPT = (
    "You are a precise job description parser. Extract ONLY information "
    "explicitly stated in the text. Return valid JSON only. Do not infer or "
    "hallucinate. Do not wrap the JSON in markdown code fences."
)

USER_PROMPT_TEMPLATE = """Parse the following job description into JSON with these exact keys:
- "role" (string): the job title
- "skills_must_have" (array of strings): required/must-have skills
- "skills_nice_to_have" (array of strings): nice-to-have/preferred skills
- "experience_required" (number): minimum years of experience required (0 if not specified)
- "location" (string): job location ("Remote" if not specified)

JD Text:
{jd_text}
"""


async def parse_jd(jd_text: str) -> dict:
    """
    Parse a raw job description into structured data.
    Primary: Groq Mixtral. Fallback: regex/keyword extraction.
    """
    try:
        if llm.available:
            logger.info("Parsing JD via Groq/Mixtral...")
            result = await llm.generate_json(
                prompt=USER_PROMPT_TEMPLATE.format(jd_text=jd_text),
                system=SYSTEM_PROMPT,
            )
            # Validate and normalise the result
            parsed = _normalise(result)
            logger.info(f"JD parsed via LLM: role='{parsed['role']}', "
                        f"{len(parsed['skills_must_have'])} must-have skills")
            return parsed
    except Exception as e:
        logger.warning(f"LLM JD parsing failed, falling back to regex: {e}")

    # ── Fallback: regex-based extraction ──────────────────────────────────
    logger.info("Parsing JD via fallback (regex)...")
    return _fallback_parse(jd_text)


def _normalise(data: dict) -> dict:
    """Ensure all expected keys exist with correct types."""
    return {
        "role": str(data.get("role", "Software Engineer")),
        "skills_must_have": list(data.get("skills_must_have", [])),
        "skills_nice_to_have": list(data.get("skills_nice_to_have", [])),
        "experience_required": _safe_int(data.get("experience_required", 0)),
        "location": str(data.get("location", "Remote")),
    }


def _safe_int(val) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _fallback_parse(jd_text: str) -> dict:
    """Regex/keyword-based JD parser (no LLM needed)."""
    text_lower = jd_text.lower()

    # ── Extract role ──
    role = "Software Engineer"
    role_patterns = [
        r"(?:role|position|title|hiring\s+for)[:\s]+([^\n,\.]+)",
        r"^([A-Z][^\n]{5,60})\n",  # First line if capitalised
    ]
    for pat in role_patterns:
        m = re.search(pat, jd_text, re.IGNORECASE | re.MULTILINE)
        if m:
            role = m.group(1).strip()
            break

    # ── Extract skills ──
    found_skills = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    # Split into must-have (first 70%) and nice-to-have (rest)
    split_point = max(1, int(len(found_skills) * 0.7))
    must_have = found_skills[:split_point]
    nice_to_have = found_skills[split_point:]

    # ── Extract experience ──
    exp_years = 0
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience)?",
                          text_lower)
    if exp_match:
        exp_years = int(exp_match.group(1))

    # ── Extract location ──
    location = "Remote"
    loc_match = re.search(r"(?:location|based\s+in|office)[:\s]+([^\n,\.]+)",
                          jd_text, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()
    elif "remote" in text_lower:
        location = "Remote"

    return {
        "role": role,
        "skills_must_have": must_have,
        "skills_nice_to_have": nice_to_have,
        "experience_required": exp_years,
        "location": location,
    }
