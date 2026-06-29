"""
Language Detection: Identifies language of extracted text.
Supports Hindi-English mixed text handling with Unicode preservation.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# Minimum text length for reliable detection
MIN_TEXT_FOR_DETECTION = 50

# Hindi Unicode range: U+0900 to U+097F (Devanagari)
HINDI_CHAR_PATTERN = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> Tuple[str, bool]:
    """
    Detect the primary language of the text.

    Returns:
        (language_code, is_mixed) e.g., ("en", False) or ("hi", True)
    """
    if not text or len(text.strip()) < MIN_TEXT_FOR_DETECTION:
        return "en", False

    # Check for Hindi characters first (quick Unicode check)
    hindi_chars = len(HINDI_CHAR_PATTERN.findall(text))
    total_chars = len([c for c in text if c.isalpha()])

    if total_chars == 0:
        return "en", False

    hindi_ratio = hindi_chars / total_chars

    if hindi_ratio > 0.5:
        return "hi", False
    if hindi_ratio > 0.1:
        return "hi-en", True  # Mixed

    # Try langdetect for other languages
    try:
        from langdetect import detect, LangDetectException
        detected = detect(text)
        return detected, False
    except ImportError:
        pass
    except Exception:
        pass

    return "en", False


def flag_mixed_language(text: str) -> dict:
    """
    Returns a language metadata dict for inclusion in JSON output.
    Flags mixed Hindi-English for special handling.
    """
    lang, is_mixed = detect_language(text)
    return {
        "language": lang,
        "is_mixed_language": is_mixed,
        "hindi_chars_present": bool(HINDI_CHAR_PATTERN.search(text)),
    }
