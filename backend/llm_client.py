"""
ScoutAI — Ollama Mistral LLM Client
Wraps Ollama's REST API with automatic fallback for when Ollama is unavailable.
"""

import httpx
import json
import logging
from backend.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    OLLAMA_TIMEOUT, OLLAMA_TEMPERATURE, OLLAMA_NUM_CTX
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """Wrapper for Ollama's local REST API using Mistral 7B."""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.available = self._check_availability()
        if self.available:
            logger.info(f"✅ Ollama connected — model '{self.model}' ready")
        else:
            logger.warning("⚠️  Ollama unavailable — running in fallback mode")

    def _check_availability(self) -> bool:
        """Check if Ollama is running and Mistral is available."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self.model in m for m in models)
        except Exception:
            return False

    def refresh_status(self) -> bool:
        """Re-check Ollama availability (useful after restart)."""
        self.available = self._check_availability()
        return self.available

    async def generate(self, prompt: str, system: str = "") -> str:
        """
        Send prompt to Mistral via Ollama. Returns generated text.
        Raises Exception on failure so callers can fall back.
        """
        if not self.available:
            raise ConnectionError("Ollama is not available")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_ctx": OLLAMA_NUM_CTX,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def generate_json(self, prompt: str, system: str = "") -> dict:
        """
        Generate and parse JSON from Mistral.
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
llm = OllamaClient()
