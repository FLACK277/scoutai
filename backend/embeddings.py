"""
ScoutAI — Embedding & FAISS Index Manager
Provides sentence-transformer embeddings and FAISS vector similarity search.
"""

import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from backend.config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages sentence-transformer model and FAISS index."""

    def __init__(self):
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = None
        self._id_map: list[int] = []  # maps FAISS position → candidate index
        logger.info("✅ Embedding model loaded")

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text to a normalized embedding vector."""
        vec = self.model.encode([text], normalize_embeddings=True)
        return vec[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode a batch of texts to normalized embedding vectors."""
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def build_index(self, embeddings: np.ndarray, ids: list[int] | None = None):
        """
        Build a FAISS index from a matrix of embeddings.
        Uses Inner Product (cosine sim on normalized vectors).
        """
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))
        self._id_map = ids if ids else list(range(len(embeddings)))
        logger.info(f"✅ FAISS index built — {self.index.ntotal} vectors, dim={dim}")

    def search(self, query_vec: np.ndarray, top_k: int = 20) -> list[tuple[int, float]]:
        """
        Search the FAISS index. Returns list of (candidate_index, similarity_score).
        """
        if self.index is None:
            logger.warning("FAISS index not built yet")
            return []
        query_vec = query_vec.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._id_map):
                results.append((self._id_map[idx], float(score)))
        return results


# Singleton instance
embedding_manager = EmbeddingManager()
