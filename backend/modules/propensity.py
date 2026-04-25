"""
ScoutAI — Module 6: Propensity-to-Switch Model
Calculates likelihood of a candidate switching jobs based on tenure at current role.
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def compute_propensity(candidate: dict) -> dict:
    """
    Compute propensity-to-switch score (0–100) based on tenure at current job.

    < 6 months  → Low propensity (20–40) — just joined, unlikely to switch
    6–18 months → Neutral (50–65) — settling in, could be open
    > 18 months → High propensity (70–95) — likely open to new opportunities

    Returns dict with score, months_at_job, and label.
    """
    joined_str = candidate.get("joined_current_job", "")
    months = _months_at_job(joined_str)

    if months < 6:
        # Just joined — very unlikely to switch
        score = 20 + (months / 6) * 20  # 20–40
        label = "Low"
        reason = f"Joined current role {months} months ago — recently started"
    elif months <= 18:
        # Settling in — could be open
        progress = (months - 6) / 12  # 0 → 1 over the 6-18 range
        score = 50 + progress * 15  # 50–65
        label = "Moderate"
        reason = f"At current role for {months} months — may be open to opportunities"
    else:
        # Long tenure — likely open to change
        progress = min((months - 18) / 24, 1.0)  # saturates at 42 months
        score = 70 + progress * 25  # 70–95
        label = "High"
        reason = f"At current role for {months} months — likely open to new challenges"

    score = round(min(max(score, 0), 100), 1)

    result = {
        "propensity_score": score,
        "months_at_job": months,
        "propensity_label": label,
        "propensity_reason": reason,
    }

    logger.debug(f"Propensity for {candidate.get('name', '?')}: "
                 f"{score} ({label}) — {months} months at job")
    return result


def compute_propensity_batch(candidates: list[dict]) -> list[dict]:
    """Compute propensity for a list of candidates."""
    results = []
    for c in candidates:
        prop = compute_propensity(c)
        results.append({
            "candidate_id": c["id"],
            "name": c["name"],
            **prop,
        })
    return results


def _months_at_job(joined_date_str: str) -> int:
    """Calculate months between join date and today."""
    if not joined_date_str:
        return 24  # default to moderate-high if unknown

    try:
        joined = datetime.strptime(joined_date_str, "%Y-%m-%d").date()
        today = date.today()
        delta = (today.year - joined.year) * 12 + (today.month - joined.month)
        return max(delta, 0)
    except (ValueError, TypeError):
        return 24  # default
