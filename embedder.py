"""
Embedding model wrapper with caching support.
"""
import os
import hashlib
import logging
import numpy as np
from typing import List, Union, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running in offline test mode
OFFLINE_MODE = os.getenv("SENTENCE_TRANSFORMERS_OFFLINE", "0") == "1"


class Embedder:
    """
    Wrapper for sentence embedding model with caching.
    Supports offline mode for testing.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = ".cache"):
        """
        Initialize embedder with optional caching.
        
        Args:
            model_name: Name of the sentence-transformers model
            cache_dir: Directory for caching embeddings
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.embedding_cache_file = self.cache_dir / "embeddings.npz"
        self.embedding_cache = {}
        
        # Load existing cache
        self._load_cache()
        
        # Initialize model (skip in offline mode)
        if OFFLINE_MODE:
            logger.info("Running in OFFLINE mode - using deterministic embeddings")
            self.model = None
        else:
            logger.info(f"Loading embedding model: {model_name}")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info("Model loaded successfully")
    
    def _load_cache(self):
        """Load cached embeddings from disk."""
        if self.embedding_cache_file.exists():
            try:
                data = np.load(self.embedding_cache_file, allow_pickle=True)
                self.embedding_cache = data.get('cache', {}).item()
                logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.embedding_cache = {}
    
    def _save_cache(self):
        """Save embeddings cache to disk."""
        try:
            np.savez(self.embedding_cache_file, cache=np.array(self.embedding_cache, dtype=object))
            logger.debug(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text to use as cache key."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _deterministic_embedding(self, text: str) -> np.ndarray:
        """
        Generate deterministic embedding for testing (offline mode).
        Uses hash of text to generate reproducible vector.
        """
        # Use hash to seed random generator for reproducibility
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(hash_val)
        
        # Generate 384-dimensional vector (same as all-MiniLM-L6-v2)
        embedding = rng.randn(384)
        
        # Normalize to unit length (like real embeddings)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.astype(np.float32)
    
    def encode(self, texts: Union[str, List[str]], use_cache: bool = True) -> np.ndarray:
        """
        Encode text(s) to embeddings.
        
        Args:
            texts: Single text or list of texts
            use_cache: Whether to use/update cache
            
        Returns:
            Embedding array (single vector or batch)
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        embeddings = []
        texts_to_encode = []
        indices_to_encode = []
        
        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            
            if use_cache and text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
            else:
                embeddings.append(None)
                texts_to_encode.append(text)
                indices_to_encode.append(i)
        
        # Encode uncached texts
        if texts_to_encode:
            if OFFLINE_MODE:
                # Use deterministic embeddings for testing
                new_embeddings = [self._deterministic_embedding(t) for t in texts_to_encode]
            else:
                if self.model is None:
                    raise RuntimeError("Model not initialized. Cannot encode texts.")
                new_embeddings = self.model.encode(texts_to_encode, convert_to_numpy=True)
            
            # Update cache and results
            for idx, text, emb in zip(indices_to_encode, texts_to_encode, new_embeddings):
                text_hash = self._hash_text(text)
                if use_cache:
                    self.embedding_cache[text_hash] = emb
                embeddings[idx] = emb
            
            # Save cache periodically
            if use_cache and len(texts_to_encode) > 0:
                self._save_cache()
        
        embeddings = np.array(embeddings)
        
        if is_single:
            return embeddings[0]
        return embeddings


# Global embedder instance
_embedder = None


def get_embedder(model_name: Optional[str] = None) -> Embedder:
    """Get or create global embedder instance."""
    global _embedder
    
    if _embedder is None:
        if model_name is None:
            model_name = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
        _embedder = Embedder(model_name)
    
    return _embedder
