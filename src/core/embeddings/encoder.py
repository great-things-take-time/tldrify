"""OpenAI Embedding Service with batch processing and caching."""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

from openai import AsyncOpenAI, OpenAI
from openai.types import CreateEmbeddingResponse
import tiktoken

from ...core.config import settings
from ...db.redis_client import redis_client

logger = logging.getLogger(__name__)


class EmbeddingEncoder:
    """
    OpenAI Embedding service with:
    - Batch processing for efficiency
    - Redis caching with TTL
    - Exponential backoff retry
    - Cost tracking
    - Model versioning
    """

    # Model configurations
    MODELS = {
        "text-embedding-3-large": {
            "dimensions": 1536,
            "max_tokens": 8191,
            "price_per_1k_tokens": 0.00013,  # USD
        },
        "text-embedding-3-small": {
            "dimensions": 512,
            "max_tokens": 8191,
            "price_per_1k_tokens": 0.00002,
        },
        "text-embedding-ada-002": {
            "dimensions": 1536,
            "max_tokens": 8191,
            "price_per_1k_tokens": 0.00010,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        batch_size: int = 100,
        cache_ttl: int = 604800,  # 7 days in seconds
        max_retries: int = 3,
        enable_cache: bool = True,
        dimensions: Optional[int] = None,  # For dimension reduction
    ):
        """
        Initialize embedding encoder.

        Args:
            api_key: OpenAI API key
            model: Model name to use
            batch_size: Maximum texts per batch
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum retry attempts
            enable_cache: Enable Redis caching
            dimensions: Target dimensions (for models that support it)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.batch_size = batch_size
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.dimensions = dimensions

        # Model configuration
        self.model_config = self.MODELS.get(model)
        if not self.model_config:
            raise ValueError(f"Unsupported model: {model}")

        # Initialize clients
        self.sync_client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # Token encoder for counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"Initialized EmbeddingEncoder with model: {model}")

    def _get_cache_key(self, text: str, model: str = None) -> str:
        """Generate cache key for text."""
        model = model or self.model
        # Include model and dimensions in cache key
        key_string = f"{model}:{self.dimensions}:{text}"
        hash_digest = hashlib.sha256(key_string.encode()).hexdigest()
        return f"embedding:{hash_digest}"

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    def _calculate_cost(self, token_count: int) -> float:
        """Calculate embedding cost."""
        price_per_token = self.model_config["price_per_1k_tokens"] / 1000
        return token_count * price_per_token

    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available."""
        if not self.enable_cache:
            return None

        try:
            cache_key = self._get_cache_key(text)
            cached_data = await redis_client.get_async(cache_key)

            if cached_data:
                self.cache_hits += 1
                # Parse cached embedding
                embedding_data = json.loads(cached_data)
                return embedding_data["embedding"]
            else:
                self.cache_misses += 1
                return None

        except Exception as e:
            logger.warning(f"Cache retrieval error: {str(e)}")
            return None

    async def _cache_embedding(
        self, text: str, embedding: List[float], metadata: Dict = None
    ):
        """Cache embedding with metadata."""
        if not self.enable_cache:
            return

        try:
            cache_key = self._get_cache_key(text)
            cache_data = {
                "embedding": embedding,
                "model": self.model,
                "dimensions": len(embedding),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            await redis_client.set_async(
                cache_key, json.dumps(cache_data), ttl=self.cache_ttl
            )

        except Exception as e:
            logger.warning(f"Cache storage error: {str(e)}")

    async def _embed_with_retry(
        self, texts: List[str], attempt: int = 0
    ) -> Optional[CreateEmbeddingResponse]:
        """Embed texts with exponential backoff retry."""
        try:
            # Prepare request parameters
            params = {
                "model": self.model,
                "input": texts,
            }

            # Add dimensions parameter if specified (for v3 models)
            if self.dimensions and "3" in self.model:
                params["dimensions"] = self.dimensions

            # Make API call
            response = await self.async_client.embeddings.create(**params)
            return response

        except Exception as e:
            if attempt < self.max_retries:
                # Exponential backoff: 2^attempt seconds
                wait_time = 2**attempt
                logger.warning(
                    f"Embedding attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {wait_time} seconds..."
                )
                await asyncio.sleep(wait_time)
                return await self._embed_with_retry(texts, attempt + 1)
            else:
                logger.error(f"Max retries exceeded. Error: {str(e)}")
                raise

    async def embed_texts(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
        use_cache: bool = True,
    ) -> List[Tuple[List[float], Dict]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            metadata: Optional metadata for each text
            use_cache: Whether to use cache

        Returns:
            List of (embedding, metadata) tuples
        """
        if not texts:
            return []

        results = []
        texts_to_embed = []
        text_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache and self.enable_cache:
                cached_embedding = await self._get_cached_embedding(text)
                if cached_embedding:
                    meta = metadata[i] if metadata else {}
                    results.append((cached_embedding, meta))
                    continue

            texts_to_embed.append(text)
            text_indices.append(i)

        # Process uncached texts in batches
        for batch_start in range(0, len(texts_to_embed), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(texts_to_embed))
            batch_texts = texts_to_embed[batch_start:batch_end]

            # Count tokens for cost tracking
            batch_tokens = sum(self._count_tokens(text) for text in batch_texts)
            self.total_tokens += batch_tokens

            # Generate embeddings
            try:
                response = await self._embed_with_retry(batch_texts)

                # Process response
                for i, embedding_data in enumerate(response.data):
                    text_idx = text_indices[batch_start + i]
                    embedding = embedding_data.embedding
                    meta = metadata[text_idx] if metadata else {}

                    # Cache the embedding
                    if use_cache and self.enable_cache:
                        await self._cache_embedding(
                            texts_to_embed[batch_start + i], embedding, meta
                        )

                    results.append((embedding, meta))

                # Update cost tracking
                batch_cost = self._calculate_cost(batch_tokens)
                self.total_cost += batch_cost

                logger.debug(
                    f"Embedded batch of {len(batch_texts)} texts "
                    f"({batch_tokens} tokens, ${batch_cost:.6f})"
                )

            except Exception as e:
                logger.error(f"Failed to embed batch: {str(e)}")
                # Return None embeddings for failed batch
                for i in range(len(batch_texts)):
                    text_idx = text_indices[batch_start + i]
                    meta = metadata[text_idx] if metadata else {}
                    results.append((None, meta))

        return results

    async def embed_text(
        self, text: str, metadata: Optional[Dict] = None, use_cache: bool = True
    ) -> Tuple[Optional[List[float]], Dict]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            metadata: Optional metadata
            use_cache: Whether to use cache

        Returns:
            (embedding, metadata) tuple
        """
        results = await self.embed_texts(
            texts=[text],
            metadata=[metadata] if metadata else None,
            use_cache=use_cache,
        )
        return results[0] if results else (None, {})

    def embed_texts_sync(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
        use_cache: bool = True,
    ) -> List[Tuple[List[float], Dict]]:
        """Synchronous version of embed_texts."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.embed_texts(texts, metadata, use_cache)
            )
        finally:
            loop.close()

    def embed_text_sync(
        self, text: str, metadata: Optional[Dict] = None, use_cache: bool = True
    ) -> Tuple[Optional[List[float]], Dict]:
        """Synchronous version of embed_text."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.embed_text(text, metadata, use_cache)
            )
        finally:
            loop.close()

    def reduce_dimensions(
        self, embeddings: List[List[float]], target_dim: int = 768
    ) -> List[List[float]]:
        """
        Reduce embedding dimensions using PCA.

        Args:
            embeddings: List of embeddings
            target_dim: Target dimension size

        Returns:
            Reduced embeddings
        """
        if not embeddings or len(embeddings[0]) <= target_dim:
            return embeddings

        try:
            from sklearn.decomposition import PCA

            # Convert to numpy array
            embeddings_array = np.array(embeddings)

            # Apply PCA
            pca = PCA(n_components=target_dim)
            reduced = pca.fit_transform(embeddings_array)

            logger.info(
                f"Reduced dimensions from {len(embeddings[0])} to {target_dim} "
                f"(explained variance: {sum(pca.explained_variance_ratio_):.2%})"
            )

            return reduced.tolist()

        except ImportError:
            logger.warning("scikit-learn not installed. Cannot reduce dimensions.")
            return embeddings
        except Exception as e:
            logger.error(f"Dimension reduction failed: {str(e)}")
            return embeddings

    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0
        )

        return {
            "model": self.model,
            "dimensions": self.dimensions or self.model_config["dimensions"],
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(cache_hit_rate, 3),
            "avg_cost_per_1k_tokens": self.model_config["price_per_1k_tokens"],
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.total_cost = 0.0
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0


class EmbeddingService:
    """
    High-level embedding service with model selection and fallback.
    """

    def __init__(self):
        """Initialize embedding service with multiple models."""
        self.primary_encoder = None
        self.fallback_encoder = None

        # Initialize primary encoder (text-embedding-3-large)
        if settings.OPENAI_API_KEY:
            try:
                self.primary_encoder = EmbeddingEncoder(
                    model="text-embedding-3-large",
                    batch_size=100,
                    dimensions=1536,  # Full dimensions
                )
                logger.info("Primary encoder initialized: text-embedding-3-large")
            except Exception as e:
                logger.error(f"Failed to initialize primary encoder: {str(e)}")

            # Initialize fallback encoder (ada-002 for cost optimization)
            try:
                self.fallback_encoder = EmbeddingEncoder(
                    model="text-embedding-ada-002",
                    batch_size=100,
                )
                logger.info("Fallback encoder initialized: text-embedding-ada-002")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback encoder: {str(e)}")

    async def embed_document_chunks(
        self,
        chunks: List[Dict[str, Any]],
        use_fallback: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of chunk dictionaries with 'content' field
            use_fallback: Use cheaper fallback model

        Returns:
            Chunks with added 'embedding' field
        """
        encoder = self.fallback_encoder if use_fallback else self.primary_encoder

        if not encoder:
            logger.error("No encoder available")
            return chunks

        # Extract texts and metadata
        texts = [chunk.get("content", "") for chunk in chunks]
        metadata = [
            {
                "chunk_id": chunk.get("chunk_id"),
                "document_id": chunk.get("document_id"),
                "chunk_index": chunk.get("chunk_index"),
            }
            for chunk in chunks
        ]

        # Generate embeddings
        embeddings = await encoder.embed_texts(texts, metadata)

        # Add embeddings to chunks
        for i, (embedding, _) in enumerate(embeddings):
            if embedding:
                chunks[i]["embedding"] = embedding
                chunks[i]["embedding_model"] = encoder.model
                chunks[i]["embedding_dimensions"] = len(embedding)

        return chunks

    def get_encoder_statistics(self) -> Dict[str, Any]:
        """Get statistics from all encoders."""
        stats = {}

        if self.primary_encoder:
            stats["primary"] = self.primary_encoder.get_statistics()

        if self.fallback_encoder:
            stats["fallback"] = self.fallback_encoder.get_statistics()

        return stats


# Global instance
embedding_service = EmbeddingService()