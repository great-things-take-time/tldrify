"""Qdrant vector database client and operations."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
    UpdateStatus,
    CollectionStatus,
    PointIdsList,
    CreateAlias,
    DeleteAlias,
    Batch,
    ScoredPoint,
    HasIdCondition,
    IsEmptyCondition,
    MatchAny,
    Range,
    DatetimeRange,
    OrderBy,
    Direction,
    QuantizationConfig,
    ScalarQuantization,
    HnswConfigDiff,
    OptimizersConfigDiff,
    CreateCollection,
    UpdateCollection,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from ..core.config import settings

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Qdrant vector database client with connection pooling and retry logic."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        grpc_port: int = None,
        api_key: str = None,
        https: bool = False,
        timeout: int = 30,
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant host
            port: HTTP port
            grpc_port: gRPC port (optional, for better performance)
            api_key: API key for cloud deployment
            https: Use HTTPS
            timeout: Request timeout in seconds
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.grpc_port = grpc_port or settings.QDRANT_GRPC_PORT
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.https = https
        self.timeout = timeout

        # Initialize synchronous client
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            https=self.https,
            timeout=self.timeout,
        )

        # Initialize async client for better performance
        self.async_client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            https=self.https,
            timeout=self.timeout,
        )

        logger.info(f"Initialized Qdrant client: {self.host}:{self.port}")

    # ============= Collection Management =============

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE,
        on_disk: bool = False,
        hnsw_config: Optional[Dict] = None,
        optimizers_config: Optional[Dict] = None,
        quantization: bool = False,
    ) -> bool:
        """
        Create a new collection with specified configuration.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors (1536 for text-embedding-3-large)
            distance: Distance metric (COSINE, EUCLID, DOT)
            on_disk: Store vectors on disk for large collections
            hnsw_config: HNSW index configuration
            optimizers_config: Optimizer configuration
            quantization: Enable scalar quantization for memory optimization

        Returns:
            True if collection created successfully
        """
        try:
            # Check if collection exists
            collections = await self.async_client.get_collections()
            if any(c.name == collection_name for c in collections.collections):
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            # Default HNSW config for optimal performance
            if hnsw_config is None:
                hnsw_config = {
                    "m": 16,  # Number of edges per node
                    "ef_construct": 128,  # Build-time accuracy/speed trade-off
                    "full_scan_threshold": 10000,  # Use HNSW for collections > 10K
                }

            # Default optimizer config
            if optimizers_config is None:
                optimizers_config = {
                    "deleted_threshold": 0.2,  # Trigger optimization at 20% deleted
                    "vacuum_min_vector_number": 1000,  # Min vectors before vacuum
                    "default_segment_number": 2,  # Number of segments
                    "max_segment_size": 200000,  # Max vectors per segment
                    "memmap_threshold": 50000,  # Use memory mapping above threshold
                    "indexing_threshold": 20000,  # Start indexing above threshold
                }

            # Quantization config for memory optimization
            quantization_config = None
            if quantization:
                quantization_config = ScalarQuantization(
                    type="int8",
                    quantile=0.99,
                    always_ram=True,
                )

            # Create collection
            result = await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=on_disk,
                ),
                hnsw_config=HnswConfigDiff(**hnsw_config),
                optimizers_config=OptimizersConfigDiff(**optimizers_config),
                quantization_config=quantization_config,
            )

            logger.info(
                f"Created collection '{collection_name}' with {vector_size}D vectors"
            )
            return result

        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            result = await self.async_client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return result
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False

    async def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Get collection information and statistics."""
        try:
            info = await self.async_client.get_collection(collection_name)
            return {
                "status": info.status,
                "vectors_count": info.vectors_count if hasattr(info, 'vectors_count') else 0,
                "points_count": info.points_count if hasattr(info, 'points_count') else 0,
                "segments_count": 0,  # Not available in newer versions
                "config": {
                    "vector_size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 0,
                    "distance": info.config.params.vectors.distance if hasattr(info.config.params.vectors, 'distance') else 'cosine',
                    "on_disk": info.config.params.vectors.on_disk if hasattr(info.config.params.vectors, 'on_disk') else False,
                },
                "optimizer_status": info.optimizer_status if hasattr(info, 'optimizer_status') else {},
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None

    # ============= Vector Operations =============

    async def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
        wait: bool = True,
    ) -> List[str]:
        """
        Insert vectors with metadata into collection.

        Args:
            collection_name: Target collection
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries
            ids: Optional vector IDs (auto-generated if not provided)
            batch_size: Batch size for insertion
            wait: Wait for operation to complete

        Returns:
            List of inserted vector IDs
        """
        try:
            if len(vectors) != len(payloads):
                raise ValueError("Vectors and payloads must have same length")

            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            inserted_ids = []

            # Process in batches
            for i in range(0, len(vectors), batch_size):
                batch_vectors = vectors[i : i + batch_size]
                batch_payloads = payloads[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]

                points = [
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                    for point_id, vector, payload in zip(
                        batch_ids, batch_vectors, batch_payloads
                    )
                ]

                result = await self.async_client.upsert(
                    collection_name=collection_name,
                    points=points,
                    wait=wait,
                )

                if result.status == UpdateStatus.COMPLETED:
                    inserted_ids.extend(batch_ids)
                    logger.debug(f"Inserted batch of {len(points)} vectors")

            logger.info(f"Inserted {len(inserted_ids)} vectors into '{collection_name}'")
            return inserted_ids

        except Exception as e:
            logger.error(f"Error inserting vectors: {str(e)}")
            raise

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Collection to search
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Metadata filters
            with_payload: Include payload in results
            with_vectors: Include vectors in results

        Returns:
            List of (id, score, payload) tuples
        """
        try:
            # Build filter from conditions
            filter_obj = None
            if filter_conditions:
                must_conditions = []
                for field, value in filter_conditions.items():
                    if isinstance(value, list):
                        # Match any value in list
                        must_conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchAny(any=value),
                            )
                        )
                    elif isinstance(value, dict):
                        # Range query
                        if "min" in value or "max" in value:
                            must_conditions.append(
                                FieldCondition(
                                    key=field,
                                    range=Range(
                                        gte=value.get("min"),
                                        lte=value.get("max"),
                                    ),
                                )
                            )
                    else:
                        # Exact match
                        must_conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=value),
                            )
                        )

                if must_conditions:
                    filter_obj = Filter(must=must_conditions)

            # Perform search
            results = await self.async_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_obj,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )

            # Format results
            formatted_results = []
            for point in results:
                formatted_results.append(
                    (
                        point.id,
                        point.score,
                        point.payload if with_payload else {},
                    )
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise

    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_text: str,
        limit: int = 10,
        alpha: float = 0.5,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Hybrid search combining vector similarity and text matching.

        Args:
            collection_name: Collection to search
            query_vector: Query embedding vector
            query_text: Text query for keyword matching
            limit: Maximum number of results
            alpha: Weight for vector search (0=text only, 1=vector only)
            filter_conditions: Metadata filters

        Returns:
            List of (id, score, payload) tuples
        """
        # For now, just use vector search
        # TODO: Implement BM25 or full-text search integration
        return await self.search_vectors(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filter_conditions=filter_conditions,
        )

    async def get_vectors(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[Dict]:
        """Retrieve specific vectors by IDs."""
        try:
            points = await self.async_client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )

            return [
                {
                    "id": point.id,
                    "payload": point.payload if with_payload else None,
                    "vector": point.vector if with_vectors else None,
                }
                for point in points
            ]
        except Exception as e:
            logger.error(f"Error retrieving vectors: {str(e)}")
            return []

    async def update_vectors(
        self,
        collection_name: str,
        ids: List[str],
        payloads: List[Dict[str, Any]],
        wait: bool = True,
    ) -> bool:
        """Update vector payloads."""
        try:
            if len(ids) != len(payloads):
                raise ValueError("IDs and payloads must have same length")

            points = [
                PointStruct(id=point_id, payload=payload, vector=[])
                for point_id, payload in zip(ids, payloads)
            ]

            result = await self.async_client.overwrite_payload(
                collection_name=collection_name,
                points=points,
                wait=wait,
            )

            return result.status == UpdateStatus.COMPLETED

        except Exception as e:
            logger.error(f"Error updating vectors: {str(e)}")
            return False

    async def delete_vectors(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> bool:
        """Delete vectors by IDs or filter."""
        try:
            if ids:
                result = await self.async_client.delete(
                    collection_name=collection_name,
                    points_selector=PointIdsList(points=ids),
                    wait=wait,
                )
            elif filter_conditions:
                # Build filter
                must_conditions = []
                for field, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value),
                        )
                    )

                result = await self.async_client.delete(
                    collection_name=collection_name,
                    points_selector=Filter(must=must_conditions),
                    wait=wait,
                )
            else:
                raise ValueError("Either ids or filter_conditions must be provided")

            return result.status == UpdateStatus.COMPLETED

        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            return False

    # ============= Collection Aliases & Versioning =============

    async def create_alias(
        self, alias_name: str, collection_name: str
    ) -> bool:
        """Create or update collection alias for blue-green deployments."""
        try:
            result = await self.async_client.update_collection_aliases(
                change_aliases_operations=[
                    CreateAlias(
                        alias_name=alias_name,
                        collection_name=collection_name,
                    )
                ]
            )
            logger.info(f"Created alias '{alias_name}' -> '{collection_name}'")
            return result
        except Exception as e:
            logger.error(f"Error creating alias: {str(e)}")
            return False

    async def delete_alias(self, alias_name: str) -> bool:
        """Delete collection alias."""
        try:
            result = await self.async_client.update_collection_aliases(
                change_aliases_operations=[
                    DeleteAlias(alias_name=alias_name)
                ]
            )
            logger.info(f"Deleted alias '{alias_name}'")
            return result
        except Exception as e:
            logger.error(f"Error deleting alias: {str(e)}")
            return False

    # ============= Backup & Monitoring =============

    async def create_snapshot(self, collection_name: str) -> Optional[str]:
        """Create collection snapshot for backup."""
        try:
            result = await self.async_client.create_snapshot(
                collection_name=collection_name
            )
            logger.info(f"Created snapshot for '{collection_name}': {result.name}")
            return result.name
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}")
            return None

    async def get_cluster_info(self) -> Dict:
        """Get Qdrant cluster information."""
        try:
            info = await self.async_client.get_cluster_info()
            return {
                "version": info.version,
                "commit": info.commit,
                "collections_count": info.collections_count,
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {str(e)}")
            return {}

    async def health_check(self) -> bool:
        """Check Qdrant health status."""
        try:
            # Try to list collections as health check
            await self.async_client.get_collections()
            return True
        except Exception:
            return False

    async def close(self):
        """Close client connections."""
        if hasattr(self.async_client, "close"):
            await self.async_client.close()
        logger.info("Closed Qdrant connections")


# Global instance
vector_db = VectorDatabase()


# Context manager for async operations
@asynccontextmanager
async def get_vector_db():
    """Get vector database instance."""
    try:
        yield vector_db
    finally:
        pass  # Connection pooling handles cleanup