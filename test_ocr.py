"""Test OCR processing functionality."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.ocr.processor import OCRProcessor
from src.core.ocr.pymupdf_fallback import PyMuPDFFallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pymupdf():
    """Test PyMuPDF text extraction."""
    print("\n=== Testing PyMuPDF Fallback ===")

    # Look for a test PDF
    test_pdfs = list(Path(".").glob("*.pdf"))
    if not test_pdfs:
        print("No PDF files found in current directory")
        return

    pdf_path = str(test_pdfs[0])
    print(f"Testing with: {pdf_path}")

    fallback = PyMuPDFFallback()

    # Check if PDF has text
    has_text = fallback.check_has_text(pdf_path)
    print(f"PDF has selectable text: {has_text}")

    if has_text:
        # Extract text
        results = fallback.extract_text(pdf_path)
        print(f"Extracted {len(results)} pages")

        if results:
            first_page = results[0]
            print(f"\nFirst page preview:")
            print(f"- Confidence: {first_page['confidence_score']:.2f}")
            print(f"- Text length: {len(first_page['text_content'])} chars")
            print(f"- First 200 chars: {first_page['text_content'][:200]}...")


def test_ocr_processor():
    """Test full OCR processor."""
    print("\n=== Testing OCR Processor ===")

    # Look for a test PDF
    test_pdfs = list(Path(".").glob("*.pdf"))
    if not test_pdfs:
        print("No PDF files found in current directory")
        return

    pdf_path = str(test_pdfs[0])
    print(f"Testing with: {pdf_path}")

    # Initialize processor (CPU mode for testing)
    processor = OCRProcessor(device="cpu", enable_cache=False)

    def progress_callback(progress, current, total):
        print(f"Progress: {progress:.1f}% ({current}/{total} pages)")

    try:
        # Process document
        results = processor.process_document(
            pdf_path=pdf_path,
            document_id=1,
            use_fallback=True,
            progress_callback=progress_callback
        )

        print(f"\nProcessed {len(results)} pages")

        if results:
            # Show summary
            avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
            total_words = sum(r['word_count'] for r in results)

            print(f"\nSummary:")
            print(f"- Average confidence: {avg_confidence:.2f}")
            print(f"- Total words: {total_words}")
            print(f"- OCR engine used: {results[0]['ocr_engine']}")

            # Show first page
            first_page = results[0]
            print(f"\nFirst page:")
            print(f"- Page: {first_page['page_number']}")
            print(f"- Quality: {first_page['quality']}")
            print(f"- Words: {first_page['word_count']}")
            print(f"- Text preview: {first_page['text_content'][:300]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("TLDRify OCR Test Suite")
    print("=" * 50)

    # Test PyMuPDF first (simpler)
    test_pymupdf()

    # Test full OCR processor
    # Note: This may download Surya models on first run
    print("\nNote: Surya OCR may download models on first run (~2GB)")
    print("Skipping full OCR test for now (would download large models)")
    # Uncomment to test full OCR:
    # test_ocr_processor()

    print("\n" + "=" * 50)
    print("Testing complete!")