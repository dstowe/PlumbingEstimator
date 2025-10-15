"""
PDF Processing Service
Handles PDF to image conversion and page extraction
"""
import fitz  # PyMuPDF
import cv2
import numpy as np
from config import Config

def extract_pdf_page_as_image(pdf_path, page_num, dpi=None):
    """
    Convert PDF page to image for processing
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for conversion (default from config)
    
    Returns:
        numpy array: Image in OpenCV format (BGR)
    """
    if dpi is None:
        dpi = Config.PDF_DPI
    
    doc = fitz.open(pdf_path)
    
    if page_num >= len(doc):
        doc.close()
        raise ValueError(f"Page {page_num} does not exist in PDF")
    
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    doc.close()
    
    # Convert to OpenCV format
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    return img

def get_pdf_page_count(pdf_path):
    """
    Get the number of pages in a PDF
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        int: Number of pages
    """
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except:
        return 1

def detect_scale_notation(img):
    """
    Detect scale notation in drawing (e.g., '1/4" = 1'-0"')
    
    Args:
        img: OpenCV image
    
    Returns:
        str: Detected scale or default
    
    Note: This is a placeholder. Full implementation would use OCR (Tesseract)
    to read text from the drawing and extract scale information.
    """
    # TODO: Implement OCR-based scale detection
    # For now, return a default scale
    return "1/4\" = 1'-0\""