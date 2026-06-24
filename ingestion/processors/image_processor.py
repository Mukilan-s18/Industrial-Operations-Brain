"""
Image Processor: Handles P&ID drawings and embedded images.
Uses OpenCV to preprocess before running OCR on drawing tags.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def preprocess_pid_image(pil_image: Image.Image) -> Image.Image:
    """
    Pre-process a P&ID drawing for tag extraction:
    - Convert to grayscale
    - Increase contrast (CLAHE)
    - Apply Otsu thresholding
    """
    img = np.array(pil_image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Contrast Limited Adaptive Histogram Equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Otsu's thresholding
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def extract_image_text_from_pdf(fitz_page) -> List[str]:
    """
    Extract text from all images embedded in a PDF page.
    Useful for P&ID drawings with equipment tags.
    """
    extracted_texts: List[str] = []

    try:
        image_list = fitz_page.get_images(full=True)
        doc = fitz_page.parent

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                pil_image = Image.open(BytesIO(img_bytes)).convert("RGB")

                # Preprocess for P&ID
                processed = preprocess_pid_image(pil_image)

                # OCR with single line mode (good for tags like "P-101")
                text = pytesseract.image_to_string(
                    processed,
                    config="--psm 11 --oem 3"  # sparse text mode
                ).strip()

                if text:
                    extracted_texts.append(text)
            except Exception as e:
                logger.debug(f"Skipping image xref {xref}: {e}")

    except Exception as e:
        logger.warning(f"Failed to extract images from page: {e}")

    return extracted_texts
