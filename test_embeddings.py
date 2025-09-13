"""Test OpenAI embedding service."""

import asyncio
import os
from typing import List, Dict, Any
import time
import json
from pathlib import Path
import numpy as np

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.core.embeddings.encoder import EmbeddingEncoder, EmbeddingService
from src.core.embeddings.chunker import SemanticChunker
from src.db.vector import VectorDatabase
from src.db.models import Document, TextChunk
from src.db.base import get_db, SessionLocal
from src.core.config import settings


async def test_embedding_encoder():
    """Test the basic embedding encoder functionality."""
    print("\n=== Testing Embedding Encoder ===")

    # Check if API key exists
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    try:
        # Initialize encoder
        encoder = EmbeddingEncoder(
            model="text-embedding-3-large",
            batch_size=5,
            cache_ttl=3600,  # 1 hour for testing
            enable_cache=True,
            dimensions=1536
        )
        print(f"✅ Encoder initialized with model: {encoder.model}")

        # Test single text embedding
        test_text = "This is a test sentence for embedding generation."
        print(f"\n📝 Testing single text: '{test_text}'")

        embedding, metadata = await encoder.embed_text(test_text)

        if embedding:
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"   First 5 values: {embedding[:5]}")
            print(f"   Vector norm: {np.linalg.norm(embedding):.4f}")
        else:
            print("❌ Failed to generate embedding")
            return False

        # Test batch processing
        test_texts = [
            "Machine learning is a subset of artificial intelligence.",
            "Natural language processing enables computers to understand human language.",
            "Deep learning uses neural networks with multiple layers.",
            "Transformers have revolutionized NLP tasks.",
            "RAG combines retrieval and generation for better responses."
        ]

        print(f"\n📝 Testing batch of {len(test_texts)} texts...")
        embeddings = await encoder.embed_texts(test_texts)

        print(f"✅ Generated {len(embeddings)} embeddings")
        for i, (emb, meta) in enumerate(embeddings[:3]):
            if emb:
                print(f"   Text {i+1}: {len(emb)} dimensions")

        # Test caching
        print("\n🔄 Testing cache...")
        start_time = time.time()
        cached_embedding, _ = await encoder.embed_text(test_text)
        cache_time = time.time() - start_time

        if cached_embedding:
            print(f"✅ Cache hit! Retrieved in {cache_time:.4f} seconds")
            print(f"   Cache stats: {encoder.cache_hits} hits, {encoder.cache_misses} misses")

        # Get statistics
        stats = encoder.get_statistics()
        print(f"\n📊 Encoder Statistics:")
        print(f"   Total tokens: {stats['total_tokens']}")
        print(f"   Total cost: ${stats['total_cost']:.6f}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_service():
    """Test the high-level embedding service."""
    print("\n=== Testing Embedding Service ===")

    try:
        # Initialize service
        service = EmbeddingService()

        if not service.primary_encoder:
            print("❌ No primary encoder available")
            return False

        print(f"✅ Service initialized")
        print(f"   Primary: {service.primary_encoder.model if service.primary_encoder else 'None'}")
        print(f"   Fallback: {service.fallback_encoder.model if service.fallback_encoder else 'None'}")

        # Test document chunk embedding
        test_chunks = [
            {
                "chunk_id": "test_1",
                "document_id": 1,
                "chunk_index": 0,
                "content": "Artificial intelligence is transforming how we interact with technology.",
                "metadata": {"page": 1, "section": "Introduction"}
            },
            {
                "chunk_id": "test_2",
                "document_id": 1,
                "chunk_index": 1,
                "content": "Machine learning algorithms can learn patterns from data without explicit programming.",
                "metadata": {"page": 1, "section": "Introduction"}
            },
            {
                "chunk_id": "test_3",
                "document_id": 1,
                "chunk_index": 2,
                "content": "Deep learning models use multiple layers to progressively extract higher-level features.",
                "metadata": {"page": 2, "section": "Methodology"}
            }
        ]

        print(f"\n📝 Processing {len(test_chunks)} document chunks...")

        # Generate embeddings for chunks
        chunks_with_embeddings = await service.embed_document_chunks(
            chunks=test_chunks,
            use_fallback=False
        )

        # Check results
        embeddings_generated = sum(1 for chunk in chunks_with_embeddings if "embedding" in chunk)
        print(f"✅ Generated embeddings for {embeddings_generated}/{len(test_chunks)} chunks")

        for i, chunk in enumerate(chunks_with_embeddings):
            if "embedding" in chunk:
                print(f"   Chunk {i+1}: {chunk['embedding_dimensions']}D from {chunk['embedding_model']}")

        # Get service statistics
        stats = service.get_encoder_statistics()
        if "primary" in stats:
            print(f"\n📊 Service Statistics:")
            print(f"   Primary encoder cost: ${stats['primary']['total_cost']:.6f}")
            print(f"   Primary cache hit rate: {stats['primary']['cache_hit_rate']:.2%}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_storage_integration():
    """Test storing embeddings in Qdrant."""
    print("\n=== Testing Vector Storage Integration ===")

    try:
        # Initialize components
        encoder = EmbeddingEncoder(
            model="text-embedding-3-large",
            batch_size=5,
            dimensions=1536
        )
        vector_db = VectorDatabase()

        # Check Qdrant health
        is_healthy = await vector_db.health_check()
        if not is_healthy:
            print("❌ Qdrant is not healthy. Make sure it's running: docker-compose up -d qdrant")
            return False

        print("✅ Qdrant is healthy")

        # Create test collection
        collection_name = "test_embeddings"
        await vector_db.create_collection(
            collection_name=collection_name,
            vector_size=1536,
            on_disk=False
        )
        print(f"✅ Created collection '{collection_name}'")

        # Generate test data
        test_documents = [
            {
                "text": "Python is a versatile programming language used in data science.",
                "metadata": {"doc_id": 1, "chunk_id": 1, "page": 1}
            },
            {
                "text": "JavaScript powers interactive web applications and Node.js backends.",
                "metadata": {"doc_id": 1, "chunk_id": 2, "page": 1}
            },
            {
                "text": "Machine learning models can predict outcomes based on historical data.",
                "metadata": {"doc_id": 2, "chunk_id": 1, "page": 1}
            },
            {
                "text": "Natural language processing helps computers understand human text.",
                "metadata": {"doc_id": 2, "chunk_id": 2, "page": 2}
            }
        ]

        # Generate embeddings
        print(f"\n📝 Generating embeddings for {len(test_documents)} documents...")
        texts = [doc["text"] for doc in test_documents]
        metadatas = [doc["metadata"] for doc in test_documents]

        embeddings = await encoder.embed_texts(texts, metadatas)

        # Prepare for storage
        vectors = []
        payloads = []
        for i, (embedding, _) in enumerate(embeddings):
            if embedding:
                vectors.append(embedding)
                payloads.append({
                    "text": test_documents[i]["text"],
                    **test_documents[i]["metadata"]
                })

        print(f"✅ Generated {len(vectors)} embeddings")

        # Store in Qdrant
        print(f"\n💾 Storing vectors in Qdrant...")
        ids = await vector_db.insert_vectors(
            collection_name=collection_name,
            vectors=vectors,
            payloads=payloads
        )
        print(f"✅ Stored {len(ids)} vectors")

        # Test search
        print(f"\n🔍 Testing similarity search...")
        query_text = "How does Python help with artificial intelligence?"
        query_embedding, _ = await encoder.embed_text(query_text)

        if query_embedding:
            results = await vector_db.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.5
            )

            print(f"Query: '{query_text}'")
            print(f"Found {len(results)} similar vectors:")
            for id, score, payload in results:
                print(f"   Score: {score:.4f} - {payload.get('text', '')[:60]}...")

        # Get collection info
        info = await vector_db.get_collection_info(collection_name)
        print(f"\n📊 Collection Statistics:")
        print(f"   Vectors count: {info['vectors_count']}")
        print(f"   Points count: {info['points_count']}")

        # Clean up
        await vector_db.delete_collection(collection_name)
        print(f"\n🗑️ Cleaned up test collection")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Test the complete pipeline: chunking -> embedding -> storage."""
    print("\n=== Testing Full Pipeline ===")

    db = SessionLocal()

    try:
        # Get a test document from database
        from src.db.models import ProcessingStatus
        document = db.query(Document).filter(
            Document.status == ProcessingStatus.COMPLETED
        ).first()

        if not document:
            print("❌ No completed documents found. Please run test_ocr.py first.")
            return False

        print(f"✅ Using document: {document.filename} (ID: {document.id})")

        # Get chunks for this document
        chunks = db.query(TextChunk).filter(
            TextChunk.document_id == document.id
        ).limit(5).all()  # Limit to 5 for testing

        if not chunks:
            print("❌ No chunks found for document. Please run test_chunking.py first.")
            return False

        print(f"✅ Found {len(chunks)} chunks to process")

        # Initialize components
        service = EmbeddingService()
        vector_db = VectorDatabase()

        # Create collection for document
        collection_name = f"document_{document.id}_embeddings"
        await vector_db.create_collection(
            collection_name=collection_name,
            vector_size=1536
        )
        print(f"✅ Created collection '{collection_name}'")

        # Prepare chunk data
        chunk_data = []
        for chunk in chunks:
            chunk_data.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.text,
                "metadata": chunk.metadata or {}
            })

        # Generate embeddings
        print(f"\n📝 Generating embeddings for chunks...")
        start_time = time.time()

        chunks_with_embeddings = await service.embed_document_chunks(
            chunks=chunk_data,
            use_fallback=False
        )

        embedding_time = time.time() - start_time
        print(f"✅ Generated embeddings in {embedding_time:.2f} seconds")

        # Store in Qdrant
        vectors = []
        payloads = []

        for chunk in chunks_with_embeddings:
            if "embedding" in chunk:
                vectors.append(chunk["embedding"])
                payloads.append({
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["content"][:500],  # Store first 500 chars
                    "metadata": chunk.get("metadata", {})
                })

        if vectors:
            print(f"\n💾 Storing {len(vectors)} vectors in Qdrant...")
            ids = await vector_db.insert_vectors(
                collection_name=collection_name,
                vectors=vectors,
                payloads=payloads
            )
            print(f"✅ Stored {len(ids)} vectors successfully")

            # Test retrieval
            print(f"\n🔍 Testing retrieval...")
            test_query = "What is the main topic of this document?"

            if service.primary_encoder:
                query_embedding, _ = await service.primary_encoder.embed_text(test_query)

                if query_embedding:
                    results = await vector_db.search_vectors(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=3
                    )

                    print(f"Query: '{test_query}'")
                    print(f"Top {len(results)} results:")
                    for id, score, payload in results:
                        text_preview = payload.get('text', '')[:100]
                        print(f"   Score: {score:.4f} - {text_preview}...")

        # Get statistics
        if service.primary_encoder:
            stats = service.primary_encoder.get_statistics()
            print(f"\n📊 Pipeline Statistics:")
            print(f"   Total tokens processed: {stats['total_tokens']}")
            print(f"   Total cost: ${stats['total_cost']:.6f}")
            print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
            print(f"   Avg embedding time: {embedding_time/len(chunks):.3f} sec/chunk")

        # Clean up
        await vector_db.delete_collection(collection_name)
        print(f"\n🗑️ Cleaned up test collection")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_dimension_reduction():
    """Test dimension reduction functionality."""
    print("\n=== Testing Dimension Reduction ===")

    try:
        # Initialize encoder with reduced dimensions
        encoder = EmbeddingEncoder(
            model="text-embedding-3-large",
            dimensions=768  # Reduce from 1536 to 768
        )

        print(f"✅ Encoder initialized with {encoder.dimensions} dimensions")

        # Generate test embeddings
        test_text = "Testing dimension reduction for more efficient storage."
        embedding, _ = await encoder.embed_text(test_text)

        if embedding:
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"   Original model supports: {encoder.model_config['dimensions']} dimensions")
            print(f"   Reduced to: {len(embedding)} dimensions")

            # Test PCA reduction
            print(f"\n📊 Testing PCA reduction...")
            embeddings = [embedding] * 5  # Create multiple for PCA
            reduced = encoder.reduce_dimensions(embeddings, target_dim=256)

            if reduced and len(reduced[0]) == 256:
                print(f"✅ PCA reduction successful: {len(embedding)} -> {len(reduced[0])} dimensions")
            else:
                print(f"⚠️ PCA reduction not available (scikit-learn may not be installed)")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def main():
    """Run all embedding tests."""
    print("=" * 60)
    print("OPENAI EMBEDDING SERVICE TEST SUITE")
    print("=" * 60)

    # Check for API key
    if not settings.OPENAI_API_KEY:
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please add it to your .env file:")
        print("OPENAI_API_KEY=your-api-key-here")
        return

    # Run tests
    tests = [
        ("Basic Encoder", test_embedding_encoder),
        ("Embedding Service", test_embedding_service),
        ("Vector Storage", test_vector_storage_integration),
        ("Full Pipeline", test_full_pipeline),
        ("Dimension Reduction", test_dimension_reduction),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")

        result = await test_func()
        results.append((test_name, result))

        if not result:
            print(f"\n⚠️ {test_name} failed, skipping dependent tests")
            if test_name in ["Basic Encoder", "Embedding Service"]:
                break

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Embedding service is ready.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())