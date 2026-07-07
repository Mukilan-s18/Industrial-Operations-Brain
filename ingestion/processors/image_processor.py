"""
Image Processor: Handles P&ID drawings and embedded images.
Uses Gemini 1.5 Flash Multimodal to natively extract tags and flow information from P&ID drawings.
"""

import logging
import os
from io import BytesIO
from pathlib import Path
from typing import List
import json

from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_image_text_from_pdf(fitz_page) -> List[str]:
    """
    Extract text and structured tags from all images embedded in a PDF page.
    Uses Gemini 1.5 Flash (Multimodal) for P&ID drawings.
    """
    extracted_texts: List[str] = []
    
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set. Skipping Gemini multimodal extraction.")
        return extracted_texts

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        image_list = fitz_page.get_images(full=True)
        doc = fitz_page.parent

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                pil_image = Image.open(BytesIO(img_bytes)).convert("RGB")

                # Define the prompt for P&ID extraction
                prompt = (
                    "You are an expert industrial engineer. Analyze this P&ID (Piping and Instrumentation Diagram) "
                    "or industrial blueprint. Extract all equipment tags (like P-101, HV-205, V-101) and return them. "
                    "If there are clear relationships or flow directions, describe them briefly. "
                    "Return just a raw list of tags found."
                )

                response = model.generate_content([prompt, pil_image])
                
                text = response.text.strip()
                if text:
                    extracted_texts.append(text)
                    logger.info(f"Gemini extracted tags: {text}")

            except Exception as e:
                logger.debug(f"Skipping image xref {xref} due to Gemini error: {e}")

    except Exception as e:
        logger.warning(f"Failed to extract images from page: {e}")

    return extracted_texts
