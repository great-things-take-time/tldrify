"""Test Qdrant vector database operations."""

import asyncio
import numpy as np
from typing import List
import time
import json

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.vector import VectorDatabase


async def generate_random_vectors(num_vectors: int, dimension: int = 1536) -> List[List[float]]:
    """Generate random vectors for testing."""
    vectors = []
    for _ in range(num_vectors):
        # Generate random vector and normalize it
        vec = np.random.randn(dimension)
        vec = vec / np.linalg.norm(vec)
        vectors.append(vec.tolist())
    return vectors


async def test_collection_operations():
    """Test collection creation and management."""
    print("\n=== Testing Collection Operations ===")

    db = VectorDatabase()
    collection_name = "test_collection"

    try:
        # Create collection
        print(f"Creating collection '{collection_name}'...")
        result = await db.create_collection(
            collection_name=collection_name,
            vector_size=1536,
            on_disk=False,
            quantization=False
        )
        print(f"✅ Collection created: {result}")

        # Get collection info
        info = await db.get_collection_info(collection_name)
        print(f"📊 Collection info:")
        print(f"   Status: {info['status']}")
        print(f"   Vector size: {info['config']['vector_size']}")
        print(f"   Distance metric: {info['config']['distance']}")

        # Clean up
        await db.delete_collection(collection_name)
        print(f"🗑️ Collection deleted")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_vector_operations():
    """Test vector CRUD operations."""
    print("\n=== Testing Vector Operations ===")

    db = VectorDatabase()
    collection_name = "test_vectors"

    try:
        # Create collection
        await db.create_collection(collection_name, vector_size=128)  # Smaller for testing
        print(f"✅ Collection '{collection_name}' created")

        # Generate test vectors
        num_vectors = 10
        vectors = await generate_random_vectors(num_vectors, dimension=128)

        # Create payloads with metadata
        payloads = [
            {
                "document_id": i,
                "chunk_index": i,
                "text": f"This is test chunk {i}",
                "page_number": i // 3 + 1,
                "section": f"Section {i // 5 + 1}",
                "language": "en" if i % 2 == 0 else "ko",
            }
            for i in range(num_vectors)
        ]

        # Insert vectors
        print(f"Inserting {num_vectors} vectors...")
        ids = await db.insert_vectors(
            collection_name=collection_name,
            vectors=vectors,
            payloads=payloads,
            batch_size=5
        )
        print(f"✅ Inserted {len(ids)} vectors")

        # Wait for indexing
        await asyncio.sleep(1)

        # Search vectors
        print("\n🔍 Searching for similar vectors...")
        query_vector = vectors[0]  # Use first vector as query

        results = await db.search_vectors(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=5,
            score_threshold=0.5
        )

        print(f"Found {len(results)} similar vectors:")
        for id, score, payload in results:
            print(f"   ID: {id}, Score: {score:.4f}, Text: {payload.get('text')}")

        # Test filtering
        print("\n🔍 Searching with filters...")
        results = await db.search_vectors(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=5,
            filter_conditions={"language": "en"}
        )

        print(f"Found {len(results)} English vectors:")
        for id, score, payload in results:
            print(f"   ID: {id}, Language: {payload.get('language')}")

        # Update vectors
        print("\n📝 Updating vector metadata...")
        update_ids = ids[:2]
        update_payloads = [
            {"text": "Updated text 1", "updated": True},
            {"text": "Updated text 2", "updated": True}
        ]

        success = await db.update_vectors(
            collection_name=collection_name,
            ids=update_ids,
            payloads=update_payloads
        )
        print(f"✅ Update successful: {success}")

        # Get specific vectors
        print("\n📥 Retrieving specific vectors...")
        vectors_data = await db.get_vectors(
            collection_name=collection_name,
            ids=update_ids,
            with_payload=True
        )

        for vec_data in vectors_data:
            print(f"   ID: {vec_data['id']}, Text: {vec_data['payload'].get('text')}")

        # Delete vectors
        print("\n🗑️ Deleting vectors...")
        success = await db.delete_vectors(
            collection_name=collection_name,
            ids=update_ids
        )
        print(f"✅ Delete successful: {success}")

        # Clean up
        await db.delete_collection(collection_name)
        print(f"🗑️ Collection deleted")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_performance():
    """Test performance with larger dataset."""
    print("\n=== Testing Performance ===")

    db = VectorDatabase()
    collection_name = "test_performance"

    try:
        # Create collection with optimized settings
        await db.create_collection(
            collection_name=collection_name,
            vector_size=384,  # Smaller dimension for testing
            on_disk=False,
            hnsw_config={
                "m": 16,
                "ef_construct": 128,
                "full_scan_threshold": 10000,
            }
        )
        print(f"✅ Collection '{collection_name}' created")

        # Insert vectors in batches
        num_vectors = 1000
        batch_size = 100

        print(f"Inserting {num_vectors} vectors...")
        start_time = time.time()

        for batch_start in range(0, num_vectors, batch_size):
            batch_end = min(batch_start + batch_size, num_vectors)
            batch_vectors = await generate_random_vectors(
                batch_end - batch_start,
                dimension=384
            )

            batch_payloads = [
                {
                    "document_id": i,
                    "chunk_index": i,
                    "text": f"Performance test chunk {i}",
                }
                for i in range(batch_start, batch_end)
            ]

            await db.insert_vectors(
                collection_name=collection_name,
                vectors=batch_vectors,
                payloads=batch_payloads
            )

            print(f"   Inserted batch {batch_start//batch_size + 1}/{num_vectors//batch_size}")

        insert_time = time.time() - start_time
        print(f"✅ Insertion completed in {insert_time:.2f} seconds")
        print(f"   Rate: {num_vectors/insert_time:.1f} vectors/second")

        # Wait for indexing
        await asyncio.sleep(2)

        # Test search performance
        print("\n🔍 Testing search performance...")
        query_vector = (await generate_random_vectors(1, 384))[0]

        search_times = []
        for i in range(10):
            start_time = time.time()
            results = await db.search_vectors(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=10
            )
            search_time = time.time() - start_time
            search_times.append(search_time)

        avg_search_time = np.mean(search_times) * 1000  # Convert to ms
        print(f"✅ Average search time: {avg_search_time:.2f} ms")

        # Get collection stats
        info = await db.get_collection_info(collection_name)
        print(f"\n📊 Final collection stats:")
        print(f"   Vectors count: {info['vectors_count']}")
        print(f"   Points count: {info['points_count']}")
        print(f"   Segments count: {info['segments_count']}")

        # Clean up
        await db.delete_collection(collection_name)
        print(f"🗑️ Collection deleted")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_aliases_and_versioning():
    """Test collection aliases for blue-green deployments."""
    print("\n=== Testing Aliases & Versioning ===")

    db = VectorDatabase()

    try:
        # Create two collections (v1 and v2)
        collection_v1 = "embeddings_v1"
        collection_v2 = "embeddings_v2"
        alias_name = "embeddings_current"

        # Create v1
        await db.create_collection(collection_v1, vector_size=128)
        print(f"✅ Created {collection_v1}")

        # Create alias pointing to v1
        await db.create_alias(alias_name, collection_v1)
        print(f"✅ Alias '{alias_name}' -> '{collection_v1}'")

        # Insert data to v1
        vectors = await generate_random_vectors(5, 128)
        payloads = [{"version": "v1", "index": i} for i in range(5)]
        await db.insert_vectors(collection_v1, vectors, payloads)
        print(f"✅ Inserted data to {collection_v1}")

        # Create v2
        await db.create_collection(collection_v2, vector_size=128)
        print(f"✅ Created {collection_v2}")

        # Insert data to v2
        vectors = await generate_random_vectors(5, 128)
        payloads = [{"version": "v2", "index": i} for i in range(5)]
        await db.insert_vectors(collection_v2, vectors, payloads)
        print(f"✅ Inserted data to {collection_v2}")

        # Switch alias to v2 (blue-green deployment)
        await db.create_alias(alias_name, collection_v2)
        print(f"✅ Switched alias '{alias_name}' -> '{collection_v2}'")

        # Clean up
        await db.delete_alias(alias_name)
        await db.delete_collection(collection_v1)
        await db.delete_collection(collection_v2)
        print("🗑️ Cleaned up collections and alias")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_health_and_monitoring():
    """Test health check and monitoring functions."""
    print("\n=== Testing Health & Monitoring ===")

    db = VectorDatabase()

    try:
        # Health check
        is_healthy = await db.health_check()
        print(f"✅ Health check: {'Healthy' if is_healthy else 'Unhealthy'}")

        # Cluster info
        cluster_info = await db.get_cluster_info()
        print(f"📊 Cluster info:")
        print(f"   Version: {cluster_info.get('version', 'N/A')}")
        print(f"   Collections: {cluster_info.get('collections_count', 0)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("QDRANT VECTOR DATABASE TEST SUITE")
    print("=" * 60)

    # Run tests
    await test_health_and_monitoring()
    await test_collection_operations()
    await test_vector_operations()
    await test_performance()
    await test_aliases_and_versioning()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())