"""Tests for Component D: LayeredDefenseCombiner."""

import pytest
# Pre-import sklearn so the lazy import inside sweep_thresholds doesn't time out
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score  # noqa: F401
from agentguard.defense.combiner import (
    DecisionOutcome,
    DefenseDecision,
    LayeredDefenseCombiner,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def combiner():
    """Default combiner with balanced alpha and standard thresholds."""
    return LayeredDefenseCombiner(alpha=0.5, block_threshold=0.70, escalate_threshold=0.35)


@pytest.fixture
def text_only_combiner():
    return LayeredDefenseCombiner(alpha=1.0, text_only_mode=True)


@pytest.fixture
def graph_only_combiner():
    return LayeredDefenseCombiner(alpha=0.0, graph_only_mode=True)


# ---------------------------------------------------------------------------
# Decision outcome tests
# ---------------------------------------------------------------------------

class TestDecisionOutcomes:
    def test_allow_both_low(self, combiner):
        """Both scores well below escalate threshold → ALLOW."""
        d = combiner.decide(text_score=0.1, graph_score=0.1)
        assert d.outcome == DecisionOutcome.ALLOW
        assert d.is_allowed

    def test_block_both_high(self, combiner):
        """Both scores above block threshold → BLOCK."""
        d = combiner.decide(text_score=0.9, graph_score=0.9)
        assert d.outcome == DecisionOutcome.BLOCK
        assert d.is_blocked

    def test_escalate_medium(self, combiner):
        """Combined score in escalation band → ESCALATE."""
        d = combiner.decide(text_score=0.5, graph_score=0.5)
        # combined = 0.5 * 0.5 + 0.5 * 0.5 = 0.50, which is ≥ 0.35 and < 0.70
        assert d.outcome == DecisionOutcome.ESCALATE
        assert d.is_escalated

    def test_high_text_low_graph_escalates(self, combiner):
        """High text score but no graph signal → escalation."""
        d = combiner.decide(text_score=0.8, graph_score=0.0)
        # combined = 0.5*0.8 + 0.5*0.0 = 0.40 → escalate
        assert d.outcome == DecisionOutcome.ESCALATE

    def test_block_boundary_exact(self):
        """Score exactly at block_threshold boundary → BLOCK."""
        c = LayeredDefenseCombiner(alpha=1.0, block_threshold=0.70, escalate_threshold=0.35, text_only_mode=True)
        d = c.decide(text_score=0.70)
        assert d.outcome == DecisionOutcome.BLOCK

    def test_escalate_boundary_exact(self):
        """Score exactly at escalate_threshold boundary → ESCALATE."""
        c = LayeredDefenseCombiner(alpha=1.0, block_threshold=0.70, escalate_threshold=0.35, text_only_mode=True)
        d = c.decide(text_score=0.35)
        assert d.outcome == DecisionOutcome.ESCALATE


# ---------------------------------------------------------------------------
# Combined score computation
# ---------------------------------------------------------------------------

class TestCombinedScore:
    def test_alpha_weighting(self):
        """Combined score reflects alpha weighting correctly."""
        c = LayeredDefenseCombiner(alpha=0.7, block_threshold=0.99, escalate_threshold=0.0)
        d = c.decide(text_score=1.0, graph_score=0.0)
        assert abs(d.combined_score - 0.7) < 1e-6

    def test_equal_alpha(self, combiner):
        """Alpha=0.5 gives arithmetic mean."""
        d = combiner.decide(text_score=0.6, graph_score=0.4)
        assert abs(d.combined_score - 0.5) < 1e-6

    def test_scores_clamped_below_zero(self, combiner):
        """Negative scores should be clamped to 0."""
        d = combiner.decide(text_score=-0.5, graph_score=0.0)
        assert d.text_score == 0.0

    def test_scores_clamped_above_one(self, combiner):
        """Scores > 1 should be clamped to 1."""
        d = combiner.decide(text_score=1.5, graph_score=0.0)
        assert d.text_score == 1.0


# ---------------------------------------------------------------------------
# Text-only / graph-only modes
# ---------------------------------------------------------------------------

class TestSingleComponentModes:
    def test_text_only_ignores_graph(self, text_only_combiner):
        """text_only_mode: combined == text_score regardless of graph_score."""
        d = text_only_combiner.decide(text_score=0.8, graph_score=0.0)
        assert abs(d.combined_score - 0.8) < 1e-6

    def test_graph_only_ignores_text(self, graph_only_combiner):
        """graph_only_mode: combined == graph_score regardless of text_score."""
        d = graph_only_combiner.decide(text_score=0.0, graph_score=0.9)
        assert abs(d.combined_score - 0.9) < 1e-6

    def test_text_only_blocks_on_high_score(self, text_only_combiner):
        d = text_only_combiner.decide(text_score=0.95, graph_score=0.0)
        assert d.is_blocked

    def test_graph_only_allows_low_score(self, graph_only_combiner):
        d = graph_only_combiner.decide(text_score=0.95, graph_score=0.0)
        assert d.is_allowed


# ---------------------------------------------------------------------------
# Batch interface
# ---------------------------------------------------------------------------

class TestBatchDecide:
    def test_batch_length(self, combiner):
        ts = [0.1, 0.5, 0.9]
        gs = [0.1, 0.5, 0.9]
        decisions = combiner.decide_batch(ts, gs)
        assert len(decisions) == 3

    def test_batch_outcomes(self, combiner):
        ts = [0.0, 0.52, 1.0]
        gs = [0.0, 0.52, 1.0]
        decisions = combiner.decide_batch(ts, gs)
        assert decisions[0].outcome == DecisionOutcome.ALLOW
        assert decisions[1].outcome == DecisionOutcome.ESCALATE
        assert decisions[2].outcome == DecisionOutcome.BLOCK

    def test_batch_no_graph_scores(self, combiner):
        """When graph_scores omitted, defaults to 0.0."""
        ts = [0.0, 0.8]
        decisions = combiner.decide_batch(ts)
        # 0.5*0.0 + 0.5*0.0 = 0.0 → allow
        assert decisions[0].is_allowed
        # 0.5*0.8 + 0.5*0.0 = 0.40 → escalate (≥0.35 and <0.70)
        assert decisions[1].is_escalated


# ---------------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------------

class TestParameterValidation:
    def test_invalid_alpha_raises(self):
        with pytest.raises(ValueError, match="alpha"):
            LayeredDefenseCombiner(alpha=1.5)

    def test_escalate_ge_block_raises(self):
        with pytest.raises(ValueError, match="escalate_threshold"):
            LayeredDefenseCombiner(escalate_threshold=0.8, block_threshold=0.7)

    def test_negative_alpha_raises(self):
        with pytest.raises(ValueError, match="alpha"):
            LayeredDefenseCombiner(alpha=-0.1)


# ---------------------------------------------------------------------------
# DefenseDecision helpers
# ---------------------------------------------------------------------------

class TestDefenseDecisionHelpers:
    def test_to_dict_keys(self, combiner):
        d = combiner.decide(0.2, 0.2)
        dct = d.to_dict()
        for key in ("outcome", "combined_score", "text_score", "graph_score", "alpha"):
            assert key in dct

    def test_outcome_value_in_dict(self, combiner):
        d = combiner.decide(0.05, 0.05)
        dct = d.to_dict()
        assert dct["outcome"] == "allow"

    def test_exclusive_outcome_flags(self, combiner):
        """Exactly one of is_allowed / is_escalated / is_blocked is True."""
        for ts, gs in [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)]:
            d = combiner.decide(ts, gs)
            flags = [d.is_allowed, d.is_escalated, d.is_blocked]
            assert sum(flags) == 1


# ---------------------------------------------------------------------------
# Threshold sweep
# ---------------------------------------------------------------------------

class TestThresholdSweep:
    def test_sweep_returns_list(self, combiner):
        """sweep_thresholds returns a non-empty list of dicts."""
        ts = [0.1, 0.9, 0.5]
        gs = [0.1, 0.9, 0.5]
        labels = [0, 1, 1]
        # Use explicit short list so sklearn is never invoked via the default generator
        results = combiner.sweep_thresholds(ts, gs, labels, block_thresholds=[0.3, 0.6, 0.9])
        assert isinstance(results, list)
        assert len(results) == 3

    def test_sweep_contains_expected_keys(self, combiner):
        ts = [0.0, 1.0]
        gs = [0.0, 1.0]
        labels = [0, 1]
        results = combiner.sweep_thresholds(ts, gs, labels, block_thresholds=[0.5])
        row = results[0]
        for key in ("block_threshold", "accuracy", "precision", "recall", "f1"):
            assert key in row

    def test_sweep_block_threshold_in_result(self, combiner):
        ts = [0.2, 0.8]
        gs = [0.2, 0.8]
        labels = [0, 1]
        results = combiner.sweep_thresholds(ts, gs, labels, block_thresholds=[0.4])
        assert results[0]["block_threshold"] == pytest.approx(0.4)
