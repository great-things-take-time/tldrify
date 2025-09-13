"""Surya OCR implementation for text extraction."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import io
import os

from PIL import Image
import fitz  # PyMuPDF for PDF to image conversion
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from surya.layout import LayoutPredictor

logger = logging.getLogger(__name__)


class SuryaOCR:
    """Surya OCR for multilingual text extraction."""

    def __init__(self,
                 lang_codes: List[str] = None,
                 device: str = None,
                 batch_size: int = 1):
        """
        Initialize Surya OCR.

        Args:
            lang_codes: List of language codes (e.g., ["en", "ko"])
            device: Device to run model on ("cpu" or "cuda")
            batch_size: Batch size for processing
        """
        self.lang_codes = lang_codes or ["en"]
        self.batch_size = batch_size

        # Auto-detect device if not specified
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Set environment variables for performance
        if device == "cuda":
            os.environ["TORCH_DEVICE"] = "cuda"
            # Set batch size for recognition
            os.environ["RECOGNITION_BATCH_SIZE"] = str(batch_size * 512)

        # Load models using new API
        logger.info("Loading Surya OCR models...")
        self.foundation_predictor = FoundationPredictor()
        self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
        self.detection_predictor = DetectionPredictor()
        self.layout_predictor = LayoutPredictor()

        logger.info(f"Surya OCR initialized with languages: {self.lang_codes}, device: {self.device}")

    def pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[Image.Image]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion

        Returns:
            List of PIL images
        """
        images = []
        pdf_document = fitz.open(pdf_path)

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Render page to image
            mat = fitz.Matrix(dpi/72.0, dpi/72.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)

        pdf_document.close()
        return images

    def process_page(self, image: Image.Image, page_num: int = 1) -> Dict[str, Any]:
        """
        Process a single page image with OCR.

        Args:
            image: PIL image of the page
            page_num: Page number for reference

        Returns:
            OCR result dictionary
        """
        try:
            # First detect text lines
            detection_results = self.detection_predictor([image])

            # Run OCR with detection results
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)

            if predictions and len(predictions) > 0:
                result = predictions[0]

                # Extract text and confidence
                text_content = self._extract_text_from_result(result)
                confidence_score = self._calculate_confidence(result)

                # Get layout information
                layout_results = self.layout_predictor([image])
                layout_info = self._extract_layout_info(layout_results[0] if layout_results else None)

                return {
                    "page_number": page_num,
                    "text_content": text_content,
                    "confidence_score": confidence_score,
                    "ocr_engine": "surya",
                    "language_detected": self.lang_codes[0],  # Primary language
                    "bbox_data": self._extract_bbox_data(result),
                    "layout_info": layout_info,
                    "success": True
                }
            else:
                return {
                    "page_number": page_num,
                    "text_content": "",
                    "confidence_score": 0.0,
                    "ocr_engine": "surya",
                    "success": False,
                    "error": "No text detected"
                }

        except Exception as e:
            logger.error(f"Error processing page {page_num}: {str(e)}")
            return {
                "page_number": page_num,
                "text_content": "",
                "confidence_score": 0.0,
                "ocr_engine": "surya",
                "success": False,
                "error": str(e)
            }

    def process_document(self, pdf_path: str, progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Process entire PDF document.

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates

        Returns:
            List of OCR results for each page
        """
        results = []

        # Convert PDF to images
        logger.info(f"Converting PDF to images: {pdf_path}")
        images = self.pdf_to_images(pdf_path)
        total_pages = len(images)

        logger.info(f"Processing {total_pages} pages with Surya OCR")

        for i, image in enumerate(images):
            page_num = i + 1

            # Process page
            result = self.process_page(image, page_num)
            results.append(result)

            # Report progress
            if progress_callback:
                progress = (page_num / total_pages) * 100
                progress_callback(progress, page_num, total_pages)

            logger.debug(f"Processed page {page_num}/{total_pages}, confidence: {result['confidence_score']:.2f}")

        return results

    def _extract_text_from_result(self, result: Dict) -> str:
        """Extract text content from Surya OCR result."""
        text_lines = []

        if "text_lines" in result:
            for line in result["text_lines"]:
                if "text" in line:
                    text_lines.append(line["text"])

        return "\n".join(text_lines)

    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate average confidence score from OCR result."""
        confidences = []

        if "text_lines" in result:
            for line in result["text_lines"]:
                if "confidence" in line:
                    confidences.append(line["confidence"])

        if confidences:
            return sum(confidences) / len(confidences)
        return 0.0

    def _extract_bbox_data(self, result: Dict) -> List[Dict]:
        """Extract bounding box data from OCR result."""
        bbox_data = []

        if "text_lines" in result:
            for line in result["text_lines"]:
                bbox_data.append({
                    "text": line.get("text", ""),
                    "bbox": line.get("bbox", []),
                    "polygon": line.get("polygon", []),
                    "confidence": line.get("confidence", 0.0),
                    "words": line.get("words", []),
                    "chars": line.get("chars", [])
                })

        return bbox_data

    def _extract_layout_info(self, layout_result: Dict) -> List[Dict]:
        """Extract layout information from layout detection result."""
        if not layout_result:
            return []

        layout_info = []
        if "bboxes" in layout_result:
            for i, bbox in enumerate(layout_result["bboxes"]):
                layout_info.append({
                    "bbox": bbox,
                    "polygon": layout_result.get("polygons", [[]])[i] if "polygons" in layout_result else [],
                    "label": layout_result.get("labels", [""])[i] if "labels" in layout_result else "",
                    "confidence": layout_result.get("confidences", [0.0])[i] if "confidences" in layout_result else 0.0,
                    "order": layout_result.get("order", [0])[i] if "order" in layout_result else 0
                })

        return layout_info