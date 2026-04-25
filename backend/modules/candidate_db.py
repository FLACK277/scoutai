"""
ScoutAI — Module 3: Candidate Database Manager
Loads mock candidates from JSON, builds FAISS index from resume embeddings.
"""

import json
import logging
import numpy as np
from backend.config import CANDIDATES_FILE
from backend.embeddings import embedding_manager

logger = logging.getLogger(__name__)


class CandidateDB:
    """Manages candidate data and vector index."""

    def __init__(self):
        self.candidates: list[dict] = []
        self._loaded = False

    def load(self):
        """Load candidates from JSON and build FAISS index."""
        if self._loaded:
            return

        logger.info(f"Loading candidates from {CANDIDATES_FILE}...")
        with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
            self.candidates = json.load(f)

        logger.info(f"Loaded {len(self.candidates)} candidates")

        # Build FAISS index from resume texts
        texts = [c["raw_resume_text"] for c in self.candidates]
        ids = [c["id"] for c in self.candidates]

        logger.info("Generating embeddings for candidate resumes...")
        embeddings = embedding_manager.encode_batch(texts)
        embedding_manager.build_index(np.array(embeddings), ids)

        self._loaded = True
        logger.info(f"✅ Candidate DB ready — {len(self.candidates)} candidates indexed")

    def get_by_id(self, candidate_id: int) -> dict | None:
        """Get a single candidate by ID."""
        for c in self.candidates:
            if c["id"] == candidate_id:
                return c
        return None

    def get_all(self) -> list[dict]:
        """Get all candidates."""
        return self.candidates

    def get_by_ids(self, ids: list[int]) -> list[dict]:
        """Get multiple candidates by their IDs, preserving order."""
        id_map = {c["id"]: c for c in self.candidates}
        return [id_map[cid] for cid in ids if cid in id_map]


# Singleton instance
candidate_db = CandidateDB()
