"""Create a simple test PDF for OCR testing."""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io


def create_text_pdf():
    """Create a PDF with selectable text."""
    pdf_path = "test_text.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Page 1
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "TLDRify OCR Test Document")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, "This is a test PDF document created for testing OCR functionality.")
    c.drawString(100, height - 170, "It contains selectable text that should be extracted by PyMuPDF.")

    c.setFont("Helvetica", 11)
    text = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

    Key Features:
    • Automatic text extraction
    • Multiple language support
    • Layout analysis
    • Confidence scoring
    • Fallback mechanisms

    This document tests the basic text extraction capabilities of our OCR system.
    """

    y_pos = height - 220
    for line in text.split('\n'):
        if line.strip():
            c.drawString(100, y_pos, line.strip())
            y_pos -= 15

    # Page 2
    c.showPage()
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 100, "Page 2: Technical Details")

    c.setFont("Helvetica", 11)
    tech_text = """
    OCR Processing Pipeline:
    1. PDF Loading and Validation
    2. Page Extraction
    3. Text Detection
    4. Character Recognition
    5. Post-processing and Cleaning
    6. Confidence Scoring
    7. Result Caching

    Supported Formats:
    - PDF (text-based and scanned)
    - Images (PNG, JPEG, TIFF)
    - Multi-page documents

    Performance Metrics:
    - Processing Speed: < 5 seconds per page
    - Accuracy: > 95% for high-quality documents
    - Memory Usage: Optimized for large documents
    """

    y_pos = height - 140
    for line in tech_text.split('\n'):
        if line.strip():
            c.drawString(100, y_pos, line.strip())
            y_pos -= 14

    c.save()
    print(f"Created text-based PDF: {pdf_path}")


def create_image_pdf():
    """Create a PDF with an image (simulating scanned document)."""
    pdf_path = "test_image.pdf"

    # Create an image with text
    img = Image.new('RGB', (2480, 3508), color='white')  # A4 at 300 DPI
    draw = ImageDraw.Draw(img)

    # Try to use a basic font
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
        font_normal = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()

    # Draw text on image
    draw.text((300, 300), "Scanned Document Test", font=font_large, fill='black')
    draw.text((300, 500), "This PDF contains an image with text.", font=font_normal, fill='black')
    draw.text((300, 600), "It simulates a scanned document that requires OCR.", font=font_normal, fill='black')
    draw.text((300, 700), "Surya OCR should be able to extract this text.", font=font_normal, fill='black')

    # Add some noise to simulate scan artifacts
    for i in range(100):
        x = i * 25
        draw.line([(x, 0), (x, 3508)], fill='gray', width=1)

    # Convert to PDF
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    c = canvas.Canvas(pdf_path, pagesize=(2480, 3508))
    c.drawImage(ImageReader(img_buffer), 0, 0, width=2480, height=3508)
    c.save()

    print(f"Created image-based PDF: {pdf_path}")


if __name__ == "__main__":
    print("Creating test PDFs...")

    # Check if reportlab is installed
    try:
        import reportlab
        create_text_pdf()
        create_image_pdf()
        print("\nTest PDFs created successfully!")
        print("- test_text.pdf: Contains selectable text (for PyMuPDF)")
        print("- test_image.pdf: Contains image with text (for Surya OCR)")
    except ImportError:
        print("Installing reportlab...")
        import subprocess
        subprocess.run(["uv", "add", "reportlab", "pillow"])
        print("Please run this script again after installation.")