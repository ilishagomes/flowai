import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.impact_estimator import estimate_impact


def test_basic_savings_calculation():
    result = estimate_impact(
        manual_minutes_per_run=180, ai_assisted_minutes_per_run=60,
        runs_per_week=1, hourly_rate=40,
    )
    assert result["minutes_saved_per_run"] == 120
    assert result["hours_saved_per_week"] == 2.0
    assert result["percent_time_reduction"] == 67


def test_no_negative_savings_when_ai_is_slower():
    # If AI-assisted time is somehow estimated higher than manual, we should
    # never report negative savings - clamp to zero.
    result = estimate_impact(
        manual_minutes_per_run=30, ai_assisted_minutes_per_run=45,
        runs_per_week=1, hourly_rate=40,
    )
    assert result["minutes_saved_per_run"] == 0
    assert result["percent_time_reduction"] == 0


def test_runs_per_week_scales_weekly_savings():
    result_1x = estimate_impact(120, 60, runs_per_week=1, hourly_rate=40)
    result_5x = estimate_impact(120, 60, runs_per_week=5, hourly_rate=40)
    assert result_5x["hours_saved_per_week"] == result_1x["hours_saved_per_week"] * 5


def test_zero_manual_minutes_does_not_divide_by_zero():
    result = estimate_impact(0, 0, runs_per_week=1, hourly_rate=40)
    assert result["percent_time_reduction"] == 0


def test_dollars_saved_scales_with_hourly_rate():
    low_rate = estimate_impact(180, 60, runs_per_week=1, hourly_rate=20)
    high_rate = estimate_impact(180, 60, runs_per_week=1, hourly_rate=40)
    assert high_rate["dollars_saved_per_year"] == low_rate["dollars_saved_per_year"] * 2
