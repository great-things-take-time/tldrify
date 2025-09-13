"""Test the full pipeline: Upload -> OCR -> Chunking -> Embedding -> Search"""

import requests
import json
import time
from pathlib import Path
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_pipeline(pdf_path: str):
    """Test the full document processing pipeline."""

    print("=" * 80)
    print("TLDRIFY FULL PIPELINE TEST")
    print("=" * 80)

    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return

    # 1. Upload PDF
    print("\n1️⃣ UPLOADING PDF...")
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return

    upload_result = response.json()
    document_id = upload_result.get('document_id')  # Changed from 'documentId' to 'document_id'
    print(f"✅ Upload successful! Document ID: {document_id}")
    print(f"   Filename: {upload_result.get('filename')}")
    print(f"   Size: {upload_result.get('size')} bytes")

    # 2. Process OCR (using PyMuPDF fallback for text PDFs)
    print("\n2️⃣ PROCESSING OCR...")
    ocr_response = requests.post(
        f"{BASE_URL}/api/v1/ocr/process/{document_id}",
        params={"async_processing": False, "use_fallback": True}
    )

    if ocr_response.status_code != 200:
        print(f"❌ OCR processing failed: {ocr_response.text}")
        return

    ocr_result = ocr_response.json()
    print(f"✅ OCR processing started!")
    print(f"   Message: {ocr_result.get('message')}")

    # Wait for OCR to complete (background task)
    print("   Waiting for OCR to complete...")
    time.sleep(5)  # Give enough time for OCR processing

    # Check if OCR results are saved
    ocr_check = requests.get(f"{BASE_URL}/api/v1/ocr/status/{document_id}")
    if ocr_check.status_code == 200:
        status_data = ocr_check.json()
        print(f"   Processed pages: {status_data.get('processed_pages', 0)}")
        print(f"   Status: {status_data.get('status', 'unknown')}")

    # 3. Create chunks
    print("\n3️⃣ CREATING SEMANTIC CHUNKS...")
    chunk_response = requests.post(
        f"{BASE_URL}/api/v1/chunks/process/{document_id}",
        params={
            "min_tokens": 500,
            "max_tokens": 1500,
            "overlap_tokens": 100
        }
    )

    if chunk_response.status_code != 200:
        print(f"❌ Chunking failed: {chunk_response.text}")
        return

    chunk_result = chunk_response.json()
    print(f"✅ Chunking successful! Created {chunk_result['total_chunks']} chunks")

    # 4. Get chunk statistics
    print("\n4️⃣ CHUNK STATISTICS...")
    stats_response = requests.get(f"{BASE_URL}/api/v1/chunks/{document_id}/statistics")

    if stats_response.status_code == 200:
        stats = stats_response.json()['statistics']
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Average tokens: {stats['avg_token_count']:.1f}")
        print(f"   Token range: {stats['min_token_count']} - {stats['max_token_count']}")
        print(f"   Total tokens: {stats['total_tokens']}")
        print(f"   Hierarchy levels: {stats['hierarchy_levels']}")
        if stats.get('parent_chunks'):
            print(f"   Parent chunks: {stats['parent_chunks']}")
            print(f"   Child chunks: {stats['child_chunks']}")

    # 5. Preview chunks
    print("\n5️⃣ CHUNK PREVIEW...")
    preview_response = requests.get(
        f"{BASE_URL}/api/v1/chunks/{document_id}/preview",
        params={"limit": 3}
    )

    if preview_response.status_code == 200:
        preview_data = preview_response.json()
        print(f"   Showing {len(preview_data['previews'])} of {preview_data['total_chunks']} chunks:\n")

        for i, preview in enumerate(preview_data['previews'], 1):
            print(f"   Chunk {preview['index']}:")
            print(f"   - Tokens: {preview['tokens']}")
            print(f"   - Section: {preview['section'] or 'None'}")
            print(f"   - Preview: {preview['preview'][:100]}...")
            print()

    # 6. Generate embeddings
    print("6️⃣ GENERATING EMBEDDINGS...")
    embedding_response = requests.post(
        f"{BASE_URL}/api/v1/embeddings/{document_id}/generate",
        params={"batch_size": 50, "use_cache": True}
    )

    if embedding_response.status_code != 200:
        print(f"❌ Embedding generation failed: {embedding_response.text}")
    else:
        embedding_result = embedding_response.json()
        print(f"✅ Embedding generation started!")
        print(f"   Job ID: {embedding_result.get('job_id')}")
        print(f"   Total chunks to process: {embedding_result.get('total_chunks')}")

        # Wait for embeddings to complete
        print("   Waiting for embedding generation...")
        for i in range(30):  # Wait max 30 seconds
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/v1/embeddings/{document_id}/status")

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                progress = status_data.get("progress_percentage", 0)

                print(f"   Progress: {progress:.1f}%", end="\r")

                if status == "completed":
                    print(f"\n   ✅ Embeddings generated successfully!")
                    print(f"   Total cost: ${status_data.get('total_cost', 0):.6f}")
                    print(f"   Vectors in database: {status_data.get('vector_database', {}).get('vectors_count', 0)}")
                    break
                elif status == "failed":
                    print(f"\n   ❌ Embedding generation failed: {status_data.get('error_message')}")
                    break

    # 7. Test semantic search
    print("\n7️⃣ TESTING SEMANTIC SEARCH...")
    test_queries = [
        "What is the main topic of this document?",
        "machine learning and artificial intelligence",
        "How does this work?"
    ]

    for query in test_queries[:2]:  # Test first 2 queries
        print(f"\n   🔍 Query: '{query}'")

        search_response = requests.post(
            f"{BASE_URL}/api/v1/embeddings/{document_id}/search",
            params={"query": query, "limit": 3, "score_threshold": 0.5}
        )

        if search_response.status_code == 200:
            search_results = search_response.json()
            results = search_results.get("results", [])

            if results:
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    score = result.get("score", 0)
                    text = result.get("text", "")[:80]
                    print(f"     {i}. Score: {score:.4f} - {text}...")
            else:
                print("   No results found")
        else:
            print(f"   ❌ Search failed: {search_response.text}")

    # 8. Export chunks to file
    print("\n8️⃣ EXPORTING CHUNKS TO FILE...")

    # Try different export formats
    formats = ["simple", "detailed", "debug"]

    for format_type in formats:
        export_response = requests.get(
            f"{BASE_URL}/api/v1/chunks/{document_id}/export",
            params={"format": format_type}
        )

        if export_response.status_code == 200:
            # Save the exported file
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)

            filename = f"chunks_{document_id}_{Path(pdf_path).stem}_{format_type}.txt"
            filepath = export_dir / filename

            with open(filepath, 'wb') as f:
                f.write(export_response.content)

            print(f"   ✅ Exported {format_type} format to: {filepath}")

            # Show file size
            file_size = filepath.stat().st_size
            print(f"      File size: {file_size:,} bytes")

    print("\n" + "=" * 80)
    print("✅ PIPELINE TEST COMPLETE!")
    print(f"📁 Check the 'exports' folder for the chunked text files")
    print("=" * 80)

    return document_id


def check_chunk_quality(document_id: int):
    """Additional quality checks for chunks."""
    print("\n📊 CHUNK QUALITY ANALYSIS...")

    # Get all chunks
    response = requests.get(f"{BASE_URL}/api/v1/chunks/{document_id}")

    if response.status_code != 200:
        print("❌ Failed to get chunks")
        return

    data = response.json()
    chunks = data['chunks']

    # Analyze overlap
    overlaps = []
    for i in range(len(chunks) - 1):
        current = chunks[i]['content']
        next_chunk = chunks[i + 1]['content']

        # Simple overlap check (last 100 chars of current in next)
        if len(current) > 100 and current[-100:] in next_chunk:
            overlaps.append(i)

    print(f"   Chunks with overlap: {len(overlaps)}/{len(chunks)-1}")

    # Check token distribution
    token_counts = [c['token_count'] for c in chunks]
    within_range = sum(1 for t in token_counts if 500 <= t <= 1500)

    print(f"   Chunks within target range (500-1500): {within_range}/{len(chunks)}")
    print(f"   Percentage in range: {within_range/len(chunks)*100:.1f}%")

    # Check for sections
    sections = set(c['section_title'] for c in chunks if c.get('section_title'))
    print(f"   Unique sections detected: {len(sections)}")

    if sections:
        print("   Sections found:")
        for section in list(sections)[:5]:  # Show first 5
            print(f"     - {section}")


if __name__ == "__main__":
    # Check if PDF file is provided
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        # Use test PDF if it exists
        test_pdfs = list(Path(".").glob("test_*.pdf"))
        if test_pdfs:
            pdf_file = str(test_pdfs[0])
            print(f"Using test PDF: {pdf_file}")
        else:
            print("Usage: python test_full_pipeline.py <pdf_file>")
            print("Or create a test PDF first with: python create_test_pdf.py")
            sys.exit(1)

    # Run the pipeline test
    document_id = test_pipeline(pdf_file)

    if document_id:
        # Run quality analysis
        check_chunk_quality(document_id)

        print("\n💡 TIP: Open the exported text files to review the chunks:")
        print("   - simple: Just the chunk content")
        print("   - detailed: Includes metadata like sections and pages")
        print("   - debug: Full debug information including character ranges")