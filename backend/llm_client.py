"""
ScoutAI — Groq Cloud LLM Client
Wraps Groq's fast inference API for Mixtral.
"""

import httpx
import json
import logging
from backend.config import (
    GROQ_API_KEY, GROQ_MODEL,
    LLM_TIMEOUT, LLM_TEMPERATURE
)

logger = logging.getLogger(__name__)


class GroqClient:
    """Wrapper for Groq's REST API using Mixtral."""

    def __init__(self):
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = GROQ_MODEL
        self.api_key = GROQ_API_KEY
        self.available = bool(self.api_key)
        
        if self.available:
            logger.info(f"✅ Groq connected — model '{self.model}' ready")
        else:
            logger.warning("⚠️  Groq API key missing — LLM calls will fail")

    def refresh_status(self) -> bool:
        """Re-check availability."""
        self.available = bool(self.api_key)
        return self.available

    async def generate(self, prompt: str, system: str = "") -> str:
        """
        Send prompt to Mixtral via Groq. Returns generated text.
        Raises Exception on failure so callers can fall back.
        """
        if not self.available:
            raise ConnectionError("Groq API key is missing. Check .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": LLM_TEMPERATURE,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                resp = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Groq generate failed: {e}")
            raise

    async def generate_json(self, prompt: str, system: str = "") -> dict:
        """
        Generate and parse JSON from LLM.
        Attempts to extract valid JSON from the response.
        """
        raw = await self.generate(prompt, system)
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM response, handling markdown fences."""
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            # Try array
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}")


# Singleton instance
llm = GroqClient()
