"""
impact_estimator.py

Turns the analysis into a "before vs after" business-impact summary:
time spent per run, estimated weekly/annual savings, and a rough
dollar value using a user-supplied hourly rate.

This module is intentionally NOT an LLM call. Business-impact numbers that
go in front of a manager should be simple, transparent arithmetic that a
skeptical reader can check by hand - not something the model asserts. The
AI's job upstream was to estimate the two minute figures; this module just
does the math on top of them, consistently and reproducibly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImpactEstimate:
    manual_minutes_per_run: int
    ai_assisted_minutes_per_run: int
    runs_per_week: int
    hourly_rate: float

    @property
    def minutes_saved_per_run(self) -> int:
        return max(0, self.manual_minutes_per_run - self.ai_assisted_minutes_per_run)

    @property
    def hours_saved_per_week(self) -> float:
        return round((self.minutes_saved_per_run * self.runs_per_week) / 60, 1)

    @property
    def hours_saved_per_year(self) -> float:
        return round(self.hours_saved_per_week * 48, 1)  # 48 working weeks/year

    @property
    def dollars_saved_per_year(self) -> float:
        return round(self.hours_saved_per_year * self.hourly_rate, 0)

    @property
    def percent_time_reduction(self) -> int:
        if self.manual_minutes_per_run == 0:
            return 0
        return round(100 * self.minutes_saved_per_run / self.manual_minutes_per_run)

    def as_dict(self) -> dict:
        return {
            "manual_minutes_per_run": self.manual_minutes_per_run,
            "ai_assisted_minutes_per_run": self.ai_assisted_minutes_per_run,
            "minutes_saved_per_run": self.minutes_saved_per_run,
            "runs_per_week": self.runs_per_week,
            "hours_saved_per_week": self.hours_saved_per_week,
            "hours_saved_per_year": self.hours_saved_per_year,
            "dollars_saved_per_year": self.dollars_saved_per_year,
            "percent_time_reduction": self.percent_time_reduction,
        }


def estimate_impact(manual_minutes_per_run: int, ai_assisted_minutes_per_run: int,
                     runs_per_week: int = 1, hourly_rate: float = 40.0) -> dict:
    estimate = ImpactEstimate(
        manual_minutes_per_run=max(0, int(manual_minutes_per_run)),
        ai_assisted_minutes_per_run=max(0, int(ai_assisted_minutes_per_run)),
        runs_per_week=max(1, int(runs_per_week)),
        hourly_rate=max(0.0, float(hourly_rate)),
    )
    return estimate.as_dict()
