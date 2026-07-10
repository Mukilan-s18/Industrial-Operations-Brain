import pytest
import time
from unittest.mock import MagicMock, patch
from backend.src.llm_utils import RateLimitedLLM


def test_rate_limited_llm_success():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "Success"

    with patch("time.sleep") as mock_sleep:
        rl_llm = RateLimitedLLM(mock_llm, max_retries=3, pace_seconds=1.0)
        res = rl_llm.complete("query")
        assert res == "Success"
        mock_sleep.assert_called_once_with(1.0)
        assert mock_llm.complete.call_count == 1


def test_rate_limited_llm_retry_on_429():
    mock_llm = MagicMock()
    # Fail first, succeed second
    mock_llm.complete.side_effect = [
        Exception("429 Too Many Requests. Retry in 1.5s"),
        "Success",
    ]

    with patch("time.sleep") as mock_sleep:
        rl_llm = RateLimitedLLM(mock_llm, max_retries=3, pace_seconds=1.0)
        res = rl_llm.complete("query")

        assert res == "Success"
        assert mock_llm.complete.call_count == 2
        # First sleep for 1.5 + 2 = 3.5
        # Second sleep for 1.0 (pace_seconds)
        mock_sleep.assert_any_call(3.5)
        mock_sleep.assert_any_call(1.0)


def test_rate_limited_llm_max_retries_exceeded():
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = Exception("RESOURCE_EXHAUSTED. RetryDelay: '5s'")

    with patch("time.sleep") as mock_sleep:
        rl_llm = RateLimitedLLM(mock_llm, max_retries=2, pace_seconds=1.0)
        with pytest.raises(Exception) as exc_info:
            rl_llm.complete("query")

        assert "RESOURCE_EXHAUSTED" in str(exc_info.value)
        assert mock_llm.complete.call_count == 2
        mock_sleep.assert_called_once_with(7.0)  # 5 + 2


def test_rate_limited_llm_other_exception():
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = Exception("500 Internal Error")

    with patch("time.sleep") as mock_sleep:
        rl_llm = RateLimitedLLM(mock_llm, max_retries=3, pace_seconds=1.0)
        with pytest.raises(Exception) as exc_info:
            rl_llm.complete("query")

        assert "500 Internal Error" in str(exc_info.value)
        assert mock_llm.complete.call_count == 1
        mock_sleep.assert_not_called()


def test_parse_retry_delay_default():
    delay = RateLimitedLLM._parse_retry_delay("429 RESOURCE_EXHAUSTED")
    assert delay == 45.0
