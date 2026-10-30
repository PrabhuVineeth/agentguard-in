"""Unit tests for metrics calculation and reports."""

import pytest
from agentguard.eval.metrics import compute_benchmark_metrics
from agentguard.logging.schema import TrajectoryRun, TrajectoryStep


def test_metrics_computation_empty():
    summary = compute_benchmark_metrics([])
    assert summary.total_runs == 0
    assert summary.utility == 0.0
    assert summary.asr == 0.0


def test_metrics_computation_mock_runs():
    runs = [
        # Clean run 1: success
        TrajectoryRun(
            task_id="T1",
            domain="upi_payment",
            language="en",
            is_attacked=False,
            task_success=True,
            attack_success=False,
        ),
        # Clean run 2: failure
        TrajectoryRun(
            task_id="T2",
            domain="upi_payment",
            language="en",
            is_attacked=False,
            task_success=False,
            attack_success=False,
        ),
        # Attacked run 1: exploited
        TrajectoryRun(
            task_id="T3",
            domain="irctc_ticket",
            language="en",
            is_attacked=True,
            attack_family="direct_override",
            task_success=False,
            attack_success=True,
        ),
        # Attacked run 2: defended
        TrajectoryRun(
            task_id="T4",
            domain="irctc_ticket",
            language="hi",
            is_attacked=True,
            attack_family="hidden_text",
            task_success=True,
            attack_success=False,
        ),
    ]

    summary = compute_benchmark_metrics(runs)
    assert summary.total_runs == 4
    assert summary.clean_runs == 2
    assert summary.attacked_runs == 2
    assert summary.utility == 0.5  # 1 / 2
    assert summary.asr == 0.5  # 1 / 2
    assert summary.utility_under_attack == 0.5

    # Check family breakdown
    assert "direct_override" in summary.by_family
    assert summary.by_family["direct_override"]["asr"] == 1.0
    assert "hidden_text" in summary.by_family
    assert summary.by_family["hidden_text"]["asr"] == 0.0

    # Check language breakdown
    assert "en" in summary.by_language
    assert "hi" in summary.by_language

    md_table = summary.to_markdown_table()
    assert "Breakdown by Attack Family" in md_table
    assert "Breakdown by Language" in md_table
