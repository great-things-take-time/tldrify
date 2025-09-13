"""PyMuPDF fallback for simple PDF text extraction."""

import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PyMuPDFFallback:
    """PyMuPDF fallback for simple PDF text extraction."""

    def __init__(self):
        """Initialize PyMuPDF fallback."""
        self.confidence_threshold = 0.9  # High confidence for text-based PDFs

    def extract_text(self, pdf_path: str, progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF.

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates

        Returns:
            List of extraction results for each page
        """
        results = []

        try:
            # Open PDF document
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)

            logger.info(f"Extracting text from {total_pages} pages using PyMuPDF")

            for page_num in range(total_pages):
                page = pdf_document[page_num]

                # Extract text
                text_content = page.get_text()

                # Determine if page has selectable text
                has_text = bool(text_content.strip())
                confidence = self.confidence_threshold if has_text else 0.0

                # Extract text blocks with positions
                blocks = page.get_text("dict")
                bbox_data = self._extract_bbox_from_blocks(blocks)

                result = {
                    "page_number": page_num + 1,
                    "text_content": text_content,
                    "confidence_score": confidence,
                    "ocr_engine": "pymupdf",
                    "has_selectable_text": has_text,
                    "bbox_data": bbox_data,
                    "success": True
                }

                results.append(result)

                # Report progress
                if progress_callback:
                    progress = ((page_num + 1) / total_pages) * 100
                    progress_callback(progress, page_num + 1, total_pages)

                logger.debug(f"Extracted page {page_num + 1}/{total_pages}, has_text: {has_text}")

            pdf_document.close()

        except Exception as e:
            logger.error(f"Error extracting text with PyMuPDF: {str(e)}")
            return [{
                "page_number": 0,
                "text_content": "",
                "confidence_score": 0.0,
                "ocr_engine": "pymupdf",
                "success": False,
                "error": str(e)
            }]

        return results

    def check_has_text(self, pdf_path: str) -> bool:
        """
        Quick check if PDF has selectable text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has selectable text
        """
        try:
            pdf_document = fitz.open(pdf_path)

            # Check first few pages for text
            pages_to_check = min(3, len(pdf_document))

            for page_num in range(pages_to_check):
                page = pdf_document[page_num]
                text = page.get_text()
                if text.strip():
                    pdf_document.close()
                    return True

            pdf_document.close()
            return False

        except Exception as e:
            logger.error(f"Error checking PDF text: {str(e)}")
            return False

    def _extract_bbox_from_blocks(self, blocks: Dict) -> List[Dict]:
        """Extract bounding box data from text blocks."""
        bbox_data = []

        if "blocks" in blocks:
            for block in blocks["blocks"]:
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            bbox_data.append({
                                "text": span.get("text", ""),
                                "bbox": span.get("bbox", []),
                                "font": span.get("font", ""),
                                "size": span.get("size", 0)
                            })

        return bbox_data