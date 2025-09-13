"""Main OCR processor with fallback mechanisms."""

import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json

from .surya import SuryaOCR
from .pymupdf_fallback import PyMuPDFFallback
from ...db.redis import redis_client

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Main OCR processor with Surya and PyMuPDF fallback."""

    def __init__(self,
                 device: str = None,
                 confidence_threshold: float = 0.8,
                 enable_cache: bool = True):
        """
        Initialize OCR processor.

        Args:
            device: Device for OCR models ("cpu" or "cuda")
            confidence_threshold: Minimum confidence for OCR results
            enable_cache: Enable Redis caching for OCR results
        """
        self.confidence_threshold = confidence_threshold
        self.enable_cache = enable_cache

        # Initialize OCR engines
        self.surya_ocr = SuryaOCR(lang_codes=["en", "ko"], device=device)
        self.pymupdf_fallback = PyMuPDFFallback()

        logger.info(f"OCR Processor initialized with confidence threshold: {confidence_threshold}")

    def process_document(self,
                        pdf_path: str,
                        document_id: int,
                        use_fallback: bool = True,
                        progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Process PDF document with OCR.

        Args:
            pdf_path: Path to PDF file
            document_id: Document ID for caching
            use_fallback: Use PyMuPDF if PDF has selectable text
            progress_callback: Progress callback function

        Returns:
            List of OCR results for each page
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Check cache first
        if self.enable_cache:
            cached_results = self._get_cached_results(document_id)
            if cached_results:
                logger.info(f"Using cached OCR results for document {document_id}")
                return cached_results

        results = []
        start_time = time.time()

        # Check if PDF has selectable text (for fallback)
        has_selectable_text = False
        if use_fallback:
            has_selectable_text = self.pymupdf_fallback.check_has_text(str(pdf_path))
            logger.info(f"PDF has selectable text: {has_selectable_text}")

        # Use PyMuPDF for text-based PDFs, Surya for scanned PDFs
        if has_selectable_text and use_fallback:
            logger.info("Using PyMuPDF for text extraction (PDF has selectable text)")
            results = self.pymupdf_fallback.extract_text(str(pdf_path), progress_callback)

            # Verify quality of extracted text
            avg_confidence = self._calculate_average_confidence(results)
            if avg_confidence < self.confidence_threshold:
                logger.warning(f"Low confidence from PyMuPDF ({avg_confidence:.2f}), falling back to Surya OCR")
                results = self.surya_ocr.process_document(str(pdf_path), progress_callback)
        else:
            logger.info("Using Surya OCR for text extraction")
            results = self.surya_ocr.process_document(str(pdf_path), progress_callback)

        # Post-process results
        results = self._post_process_results(results)

        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"OCR processing completed in {processing_time:.2f} seconds")

        # Add processing metadata
        for result in results:
            result["processing_time"] = processing_time / len(results)  # Per-page time
            result["document_id"] = document_id

        # Cache results
        if self.enable_cache:
            self._cache_results(document_id, results)

        return results

    def process_page(self,
                    image_path: str,
                    page_num: int = 1) -> Dict[str, Any]:
        """
        Process a single page image.

        Args:
            image_path: Path to image file
            page_num: Page number

        Returns:
            OCR result dictionary
        """
        from PIL import Image

        image = Image.open(image_path)
        result = self.surya_ocr.process_page(image, page_num)
        return self._post_process_result(result)

    def _post_process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process OCR results."""
        processed_results = []
        for result in results:
            processed_results.append(self._post_process_result(result))
        return processed_results

    def _post_process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process a single OCR result."""
        # Clean up text content
        if "text_content" in result:
            result["text_content"] = self._clean_text(result["text_content"])

        # Calculate word and character count
        text = result.get("text_content", "")
        result["word_count"] = len(text.split())
        result["char_count"] = len(text)

        # Validate confidence score
        if "confidence_score" not in result:
            result["confidence_score"] = 0.0

        # Mark as high/low quality based on confidence
        result["quality"] = "high" if result["confidence_score"] >= self.confidence_threshold else "low"

        return result

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""

        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _calculate_average_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average confidence across all pages."""
        if not results:
            return 0.0

        confidences = [r.get("confidence_score", 0.0) for r in results]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _get_cache_key(self, document_id: int) -> str:
        """Generate cache key for document."""
        return f"ocr:results:{document_id}"

    def _get_cached_results(self, document_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached OCR results from Redis."""
        if not redis_client:
            return None

        try:
            cache_key = self._get_cache_key(document_id)
            cached_data = redis_client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached results: {str(e)}")

        return None

    def _cache_results(self, document_id: int, results: List[Dict[str, Any]]) -> None:
        """Cache OCR results in Redis."""
        if not redis_client:
            return

        try:
            cache_key = self._get_cache_key(document_id)
            # Cache for 24 hours
            redis_client.setex(
                cache_key,
                86400,  # 24 hours in seconds
                json.dumps(results, default=str)
            )
            logger.debug(f"Cached OCR results for document {document_id}")
        except Exception as e:
            logger.error(f"Error caching results: {str(e)}")

    def clear_cache(self, document_id: int) -> None:
        """Clear cached results for a document."""
        if not redis_client:
            return

        try:
            cache_key = self._get_cache_key(document_id)
            redis_client.delete(cache_key)
            logger.debug(f"Cleared cache for document {document_id}")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")