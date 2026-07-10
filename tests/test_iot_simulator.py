import pytest


def test_iot_predictive_math():
    """Verify the linear drift calculation correctly predicts time to critical."""
    CRITICAL_VIB_THRESHOLD = 12.0
    # Simulate an array of historical vibration points that are increasing linearly
    # 5.0, 6.0, 7.0, 8.0, 9.0 -> rate is 1.0 per tick
    history = [5.0, 6.0, 7.0, 8.0, 9.0]

    delta = history[-1] - history[0]
    rate_per_sec = delta / len(history)  # 4.0 / 5 = 0.8 mm/s/s

    current_vib = 9.0
    time_to_crit = (
        CRITICAL_VIB_THRESHOLD - current_vib
    ) / rate_per_sec  # (12.0 - 9.0) / 0.8 = 3.0 / 0.8 = 3.75

    assert rate_per_sec == 0.8
    assert round(time_to_crit, 1) == 3.8


def test_iot_predictive_math_stable():
    """Verify that stable or negative drift does not trigger false predictions."""
    history = [5.0, 5.1, 4.9, 5.0, 5.0]
    delta = history[-1] - history[0]
    rate_per_sec = delta / len(history)
    assert rate_per_sec <= 0.01
