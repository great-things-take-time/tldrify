"""OCR processing package."""

from .processor import OCRProcessor
from .surya import SuryaOCR
from .pymupdf_fallback import PyMuPDFFallback

__all__ = [
    "OCRProcessor",
    "SuryaOCR",
    "PyMuPDFFallback",
]