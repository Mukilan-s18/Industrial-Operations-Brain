"""
OCR Processor: Converts PDF image pages to text using Tesseract.
Pre-processes images with OpenCV for better accuracy on industrial docs.
"""

import logging
import os
from io import BytesIO
from typing import Optional
import concurrent.futures

import cv2
import numpy as np
import pytesseract
from PIL import Image

from ingestion.models.schemas import PageResult

logger = logging.getLogger(__name__)

# Minimum DPI for good OCR (300 recommended)
OCR_DPI = 300
# Tesseract timeout in seconds (graceful degradation)
OCR_TIMEOUT_SECONDS = 30
# Confidence threshold below which we flag as handwritten/noisy
HANDWRITING_CONFIDENCE_THRESHOLD = 60.0


def _preprocess_image(pil_image: Image.Image) -> Image.Image:
    """
    Pre-process a PIL image for better Tesseract accuracy.
    Applies grayscale, deskew, adaptive thresholding.
    """
    # Convert to OpenCV format
    img_array = np.array(pil_image)

    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # Deskew: detect and correct rotation
    coords = np.column_stack(np.where(gray < 200))
    if len(coords) > 0:
        try:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.5:  # Only deskew if significant
                h, w = gray.shape
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(
                    gray, M, (w, h), flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
        except Exception:
            pass  # Skip deskew on failure

    # Adaptive thresholding for low-contrast scans
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    return Image.fromarray(thresh)


def _get_tesseract_confidence(data: dict) -> float:
    """Calculate mean confidence from Tesseract output data."""
    confidences = [
        float(c) for c in data.get("conf", [])
        if str(c).strip() not in ("-1", "")
    ]
    return sum(confidences) / len(confidences) if confidences else 0.0


def ocr_page(fitz_page, page_num: int) -> PageResult:
    """
    Run Tesseract OCR on a PyMuPDF page object.

    Args:
        fitz_page: fitz.Page object
        page_num: 1-indexed page number

    Returns:
        PageResult with OCR text and confidence score
    """
    warnings = []
    text = ""
    confidence: Optional[float] = None
    is_handwriting_flagged = False

    try:
        # Convert page to high-resolution pixmap
        mat = fitz_page.get_pixmap(dpi=OCR_DPI)
        img_bytes = mat.tobytes("png")
        pil_image = Image.open(BytesIO(img_bytes))

        # Pre-process
        processed = _preprocess_image(pil_image)

        def _run_tesseract():
            return pytesseract.image_to_data(
                processed,
                output_type=pytesseract.Output.DICT,
                config="--psm 6"  # Assume uniform block of text
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_tesseract)
            try:
                data = future.result(timeout=OCR_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError("Tesseract OCR timed out")

        text = " ".join(
            word for word in data["text"] if word.strip()
        )
        confidence = _get_tesseract_confidence(data)

        if confidence < HANDWRITING_CONFIDENCE_THRESHOLD:
            is_handwriting_flagged = True
            warnings.append(
                f"Page {page_num}: Low OCR confidence ({confidence:.1f}%) — "
                "possible handwriting or low quality scan"
            )

    except TimeoutError:
        logger.warning(f"Page {page_num}: OCR timed out after {OCR_TIMEOUT_SECONDS}s")
        return PageResult(
            page=page_num,
            text="",
            is_ocr=True,
            confidence=0.0,
            error=f"OCR timed out after {OCR_TIMEOUT_SECONDS}s — page skipped",
        )
    except Exception as e:
        logger.error(f"Page {page_num}: OCR failed — {e}")
        return PageResult(
            page=page_num,
            text="",
            is_ocr=True,
            confidence=0.0,
            error=str(e),
        )

    return PageResult(
        page=page_num,
        text=text.strip(),
        is_ocr=True,
        confidence=confidence,
    )
