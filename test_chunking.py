"""Test the semantic chunking system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.embeddings.chunker import SemanticChunker, ChunkConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_chunking():
    """Test basic text chunking functionality."""
    print("\n=== Testing Basic Chunking ===")

    # Sample text with structure
    sample_text = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.

## Chapter 1: Fundamentals

### 1.1 What is Machine Learning?

Machine learning algorithms build mathematical models based on training data to make predictions or decisions without being explicitly programmed to perform the task. Machine learning algorithms are used in a wide variety of applications, such as email filtering and computer vision, where it is difficult or infeasible to develop conventional algorithms to perform the needed tasks.

### 1.2 Types of Machine Learning

There are three main types of machine learning:

1. **Supervised Learning**: The algorithm learns from labeled training data, and makes predictions based on that data. Examples include:
   - Classification (spam detection, image recognition)
   - Regression (price prediction, weather forecasting)

2. **Unsupervised Learning**: The algorithm finds patterns in unlabeled data. Examples include:
   - Clustering (customer segmentation, anomaly detection)
   - Dimensionality reduction (PCA, t-SNE)

3. **Reinforcement Learning**: The algorithm learns through interaction with an environment using feedback from its own actions. Examples include:
   - Game playing (chess, Go)
   - Robotics (navigation, manipulation)

## Chapter 2: Deep Learning

Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers. These networks attempt to simulate the behavior of the human brain—albeit far from matching its ability—allowing it to "learn" from large amounts of data.

### 2.1 Neural Networks

A neural network is a series of algorithms that endeavors to recognize underlying relationships in a set of data through a process that mimics the way the human brain operates. Neural networks can adapt to changing input so the network generates the best possible result without needing to redesign the output criteria.

### 2.2 Applications

Deep learning has revolutionized many fields:

- **Computer Vision**: Image classification, object detection, facial recognition
- **Natural Language Processing**: Machine translation, sentiment analysis, chatbots
- **Speech Recognition**: Voice assistants, transcription services
- **Healthcare**: Disease diagnosis, drug discovery, personalized medicine

## Conclusion

Machine learning and deep learning continue to evolve rapidly, opening new possibilities across industries. As data becomes more abundant and computing power increases, these technologies will play an increasingly important role in shaping our future.

The key to success in machine learning is understanding both the theoretical foundations and practical applications, combined with hands-on experience in implementing and deploying models.
"""

    # Initialize chunker with custom config
    config = ChunkConfig(
        min_tokens=100,
        max_tokens=300,
        overlap_tokens=50,
        detect_structure=True,
        enable_deduplication=True
    )

    chunker = SemanticChunker(config)

    # Chunk the text
    chunks = chunker.chunk_text(sample_text)

    print(f"Created {len(chunks)} chunks from {len(sample_text)} characters")
    print(f"Total tokens: {sum(c.token_count for c in chunks)}")

    # Display chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Index: {chunk.chunk_index}")
        print(f"Tokens: {chunk.token_count}")
        print(f"Section: {chunk.section_title or 'None'}")
        print(f"Level: {chunk.chunk_level}")
        print(f"Text preview: {chunk.content[:150]}...")

    return chunks


def test_token_counting():
    """Test token counting accuracy."""
    print("\n=== Testing Token Counting ===")

    config = ChunkConfig()
    chunker = SemanticChunker(config)

    test_texts = [
        "Hello, world!",
        "Machine learning is a powerful technology.",
        "The quick brown fox jumps over the lazy dog.",
        "人工智能正在改变世界。",  # Chinese text
        "AI와 머신러닝은 미래입니다.",  # Korean text
    ]

    for text in test_texts:
        token_count = chunker.count_tokens(text)
        print(f"Text: '{text[:50]}...' -> {token_count} tokens")


def test_overlap():
    """Test sliding window overlap."""
    print("\n=== Testing Overlap ===")

    # Text with clear sentences
    text = ". ".join([f"Sentence {i}" for i in range(1, 101)]) + "."

    config = ChunkConfig(
        min_tokens=20,
        max_tokens=50,
        overlap_tokens=10
    )

    chunker = SemanticChunker(config)
    chunks = chunker.chunk_text(text)

    print(f"Created {len(chunks)} chunks")

    # Check overlap
    for i in range(len(chunks) - 1):
        current = chunks[i].content
        next_chunk = chunks[i + 1].content

        # Find overlap
        overlap_found = False
        for j in range(len(current) - 10, 0, -1):
            if current[j:] in next_chunk:
                overlap_text = current[j:]
                if len(overlap_text) > 10:  # Meaningful overlap
                    overlap_found = True
                    print(f"Chunk {i} -> {i+1} overlap: '{overlap_text[:50]}...'")
                    break

        if not overlap_found:
            print(f"Chunk {i} -> {i+1}: No significant overlap found")


def test_structure_detection():
    """Test document structure detection."""
    print("\n=== Testing Structure Detection ===")

    text = """
# Main Title

## Section 1
Content for section 1.

### Subsection 1.1
Details about subsection 1.1.

### Subsection 1.2
Details about subsection 1.2.

## Section 2
Content for section 2.

Chapter 3: Special Format
This uses a different heading format.

CHAPTER 4: ALL CAPS
Another variation of chapter heading.
"""

    config = ChunkConfig(detect_structure=True)
    chunker = SemanticChunker(config)

    # Extract structure
    structures = chunker.structure_extractor.extract_structure(text)

    print(f"Found {len(structures)} structural elements:")
    for struct in structures:
        print(f"  - {struct['type']}: {struct['title']} (level {struct['level']})")


def test_deduplication():
    """Test chunk deduplication."""
    print("\n=== Testing Deduplication ===")

    # Text with duplicate content
    text = """
This is paragraph one with some content.

This is paragraph two with different content.

This is paragraph one with some content.

This is paragraph three with unique content.

This is paragraph two with different content.
"""

    config = ChunkConfig(
        min_tokens=10,
        max_tokens=50,
        enable_deduplication=True
    )

    chunker = SemanticChunker(config)
    chunks = chunker.chunk_text(text)

    print(f"Created {len(chunks)} chunks after deduplication")

    # Show unique content
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk.content[:50]}...")


def test_statistics():
    """Test chunk statistics."""
    print("\n=== Chunk Statistics ===")

    # Load a test file if available
    test_files = list(Path(".").glob("test_*.pdf"))
    if test_files:
        # If we have OCR'd text, use it
        print("Would test with actual PDF text (requires OCR)")
    else:
        # Use sample text
        with open(__file__, 'r') as f:
            text = f.read()

        config = ChunkConfig()
        chunker = SemanticChunker(config)
        chunks = chunker.chunk_text(text)

        # Calculate statistics
        token_counts = [c.token_count for c in chunks]

        print(f"Total chunks: {len(chunks)}")
        print(f"Average tokens: {sum(token_counts) / len(token_counts):.1f}")
        print(f"Min tokens: {min(token_counts)}")
        print(f"Max tokens: {max(token_counts)}")
        print(f"Total tokens: {sum(token_counts)}")

        # Token distribution
        print("\nToken distribution:")
        print(f"  < 500: {sum(1 for t in token_counts if t < 500)}")
        print(f"  500-1000: {sum(1 for t in token_counts if 500 <= t < 1000)}")
        print(f"  1000-1500: {sum(1 for t in token_counts if 1000 <= t < 1500)}")
        print(f"  1500-2000: {sum(1 for t in token_counts if 1500 <= t < 2000)}")
        print(f"  > 2000: {sum(1 for t in token_counts if t >= 2000)}")


if __name__ == "__main__":
    print("Semantic Chunking Test Suite")
    print("=" * 50)

    # Run tests
    test_token_counting()
    chunks = test_basic_chunking()
    test_overlap()
    test_structure_detection()
    test_deduplication()
    test_statistics()

    print("\n" + "=" * 50)
    print("Testing complete!")

    # Verify chunk quality
    print("\n=== Quality Verification ===")
    if chunks:
        token_counts = [c.token_count for c in chunks]
        within_range = sum(1 for t in token_counts if 100 <= t <= 300)
        print(f"Chunks within target range (100-300 tokens): {within_range}/{len(chunks)}")

        if within_range == len(chunks):
            print("✅ All chunks are within the target token range!")
        else:
            print(f"⚠️ {len(chunks) - within_range} chunks are outside the target range")