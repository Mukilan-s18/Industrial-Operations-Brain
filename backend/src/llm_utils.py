"""
Utility: Rate-limit-aware LLM wrapper with automatic retry + backoff.
Wraps GoogleGenAI to handle 429 RESOURCE_EXHAUSTED errors gracefully.
"""
import time
import re
import sys
from llama_index.llms.gemini import Gemini


class RateLimitedLLM:
    """Wrapper around GoogleGenAI that retries on 429 rate limit errors."""

    def __init__(self, llm: Gemini, max_retries: int = 5, pace_seconds: float = 1.0):
        self.llm = llm
        self.max_retries = max_retries
        self.pace_seconds = pace_seconds

    def complete(self, prompt: str):
        """Call LLM with automatic retry on rate limit and pacing between calls."""
        for attempt in range(self.max_retries):
            try:
                result = self.llm.complete(prompt)
                # Pace successful calls to avoid hitting rate limit on next call
                time.sleep(self.pace_seconds)
                return result
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry delay from error message
                    wait = self._parse_retry_delay(error_str)
                    if attempt < self.max_retries - 1:
                        print(f"  [RATE LIMIT] Waiting {wait:.0f}s before retry ({attempt+2}/{self.max_retries})...",
                              file=sys.stderr)
                        time.sleep(wait)
                    else:
                        raise
                else:
                    raise

    @staticmethod
    def _parse_retry_delay(error_str: str) -> float:
        """Extract the retry delay from a Gemini 429 error message."""
        # Look for patterns like "retry in 41.914965148s" or "retryDelay: '41s'"
        match = re.search(r'retry\s*(?:in|Delay[\'\":\s]*)\s*(\d+\.?\d*)\s*s', error_str, re.IGNORECASE)
        if match:
            return float(match.group(1)) + 2  # Add 2s buffer
        return 45  # Default wait
