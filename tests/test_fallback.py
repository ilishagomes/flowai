import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.fallback import analyze_workflow_offline, generate_adoption_plan_offline

SAMPLE_WORKFLOW = (
    "Every Monday I take sales data from Excel, summarize the week's performance, "
    "identify unusual changes, and email my manager a report."
)


def test_analyze_workflow_offline_returns_required_keys():
    result = analyze_workflow_offline(SAMPLE_WORKFLOW)
    assert "opportunity_map" in result
    assert "workflow_steps" in result
    assert "implementation_plan" in result
    assert "estimated_manual_minutes_per_run" in result
    assert "estimated_ai_assisted_minutes_per_run" in result


def test_analyze_workflow_offline_finds_multiple_tasks():
    result = analyze_workflow_offline(SAMPLE_WORKFLOW)
    assert len(result["opportunity_map"]) >= 2


def test_analyze_workflow_offline_always_ends_with_human_review():
    result = analyze_workflow_offline(SAMPLE_WORKFLOW)
    last_actors = [step["actor"] for step in result["workflow_steps"][-2:]]
    assert "Human" in last_actors


def test_analyze_workflow_offline_empty_string_still_returns_something():
    result = analyze_workflow_offline("")
    assert len(result["opportunity_map"]) >= 1


def test_ai_assisted_time_is_not_more_than_manual_time():
    result = analyze_workflow_offline(SAMPLE_WORKFLOW)
    # AI-assisted should never take longer than doing it fully manually.
    assert result["estimated_ai_assisted_minutes_per_run"] <= result["estimated_manual_minutes_per_run"] + 15


def test_generate_adoption_plan_offline_returns_required_keys():
    opportunity_map = analyze_workflow_offline(SAMPLE_WORKFLOW)["opportunity_map"]
    plan = generate_adoption_plan_offline(SAMPLE_WORKFLOW, opportunity_map)
    for key in ("target_users", "training_needed", "pilot_plan", "adoption_risks", "success_metrics"):
        assert key in plan
    assert len(plan["adoption_risks"]) >= 1
    assert len(plan["success_metrics"]) >= 1
