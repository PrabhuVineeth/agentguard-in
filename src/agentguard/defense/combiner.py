"""Component D: Layered Defense Combiner — fuses text guardrail (B) + graph detector (C) scores.

Decision Policy
---------------
The combiner assigns one of three outcomes to each agent turn:

  ALLOW    — Both components agree the input is benign.
  BLOCK    — At least one component is highly confident the input is malicious.
  ESCALATE — Signals are contradictory or in the uncertain mid-range; the system
             asks the human operator to confirm before proceeding.

Fusion Strategy
---------------
The combined risk score is a configurable weighted sum of the text-level score
(B) and the graph-trajectory score (C):

    combined = alpha * text_score + (1 - alpha) * graph_score

where ``alpha`` ∈ [0, 1].  Decision boundaries are then:

    combined >= block_threshold  → BLOCK
    combined >= escalate_threshold (and < block) → ESCALATE
    combined <  escalate_threshold → ALLOW

The asymmetric threshold design (escalate_threshold « block_threshold) keeps
false blocks low while maintaining a human-in-the-loop safety net for
ambiguous inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class DecisionOutcome(str, Enum):
    """Three-way action output of the layered defense."""
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class DefenseDecision:
    """Structured result returned by :class:`LayeredDefenseCombiner`."""
    outcome: DecisionOutcome
    combined_score: float
    text_score: float
    graph_score: float
    alpha: float
    block_threshold: float
    escalate_threshold: float
    metadata: Dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def is_blocked(self) -> bool:
        return self.outcome == DecisionOutcome.BLOCK

    @property
    def is_escalated(self) -> bool:
        return self.outcome == DecisionOutcome.ESCALATE

    @property
    def is_allowed(self) -> bool:
        return self.outcome == DecisionOutcome.ALLOW

    def to_dict(self) -> Dict:
        return {
            "outcome": self.outcome.value,
            "combined_score": round(self.combined_score, 4),
            "text_score": round(self.text_score, 4),
            "graph_score": round(self.graph_score, 4),
            "alpha": self.alpha,
            "block_threshold": self.block_threshold,
            "escalate_threshold": self.escalate_threshold,
        }


class LayeredDefenseCombiner:
    """Component D: Combines Component-B (text) and Component-C (graph) scores.

    Parameters
    ----------
    alpha:
        Weight assigned to the text guardrail score (B).
        ``(1 - alpha)`` is then assigned to the graph trajectory score (C).
        Default ``0.5`` gives equal weight.
    block_threshold:
        Combined score at or above which the request is unconditionally blocked.
        Default ``0.70``.
    escalate_threshold:
        Combined score at or above which the request is escalated to a human.
        Must be < ``block_threshold``. Default ``0.35``.
    text_only_mode:
        If ``True``, ignore graph score and decide purely on text score
        (useful when trajectory graph is unavailable at pre-execution time).
    graph_only_mode:
        If ``True``, ignore text score and decide purely on graph score.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        block_threshold: float = 0.70,
        escalate_threshold: float = 0.35,
        text_only_mode: bool = False,
        graph_only_mode: bool = False,
    ):
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")
        if escalate_threshold >= block_threshold:
            raise ValueError(
                f"escalate_threshold ({escalate_threshold}) must be < block_threshold ({block_threshold})"
            )

        self.alpha = alpha
        self.block_threshold = block_threshold
        self.escalate_threshold = escalate_threshold
        self.text_only_mode = text_only_mode
        self.graph_only_mode = graph_only_mode

    # ------------------------------------------------------------------
    # Core inference
    # ------------------------------------------------------------------

    def decide(
        self,
        text_score: float,
        graph_score: float = 0.0,
    ) -> DefenseDecision:
        """Combine B and C scores and return a three-way defense decision.

        Parameters
        ----------
        text_score:
            Injection risk in [0, 1] from Component B (text guardrail).
        graph_score:
            Hijack probability in [0, 1] from Component C (GNN detector).
            Pass ``0.0`` when graph is not yet available (pre-execution check).

        Returns
        -------
        DefenseDecision
        """
        text_score = float(max(0.0, min(1.0, text_score)))
        graph_score = float(max(0.0, min(1.0, graph_score)))

        if self.text_only_mode:
            combined = text_score
        elif self.graph_only_mode:
            combined = graph_score
        else:
            combined = self.alpha * text_score + (1.0 - self.alpha) * graph_score

        if combined >= self.block_threshold:
            outcome = DecisionOutcome.BLOCK
        elif combined >= self.escalate_threshold:
            outcome = DecisionOutcome.ESCALATE
        else:
            outcome = DecisionOutcome.ALLOW

        return DefenseDecision(
            outcome=outcome,
            combined_score=combined,
            text_score=text_score,
            graph_score=graph_score,
            alpha=self.alpha,
            block_threshold=self.block_threshold,
            escalate_threshold=self.escalate_threshold,
            metadata={
                "text_weight": self.alpha,
                "graph_weight": 1.0 - self.alpha,
            },
        )

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def decide_batch(
        self,
        text_scores: list,
        graph_scores: Optional[list] = None,
    ) -> list:
        """Apply :meth:`decide` to a list of scores; returns list of :class:`DefenseDecision`."""
        if graph_scores is None:
            graph_scores = [0.0] * len(text_scores)
        return [
            self.decide(ts, gs)
            for ts, gs in zip(text_scores, graph_scores)
        ]

    # ------------------------------------------------------------------
    # Threshold sweep — useful for ROC / operating-point selection
    # ------------------------------------------------------------------

    def sweep_thresholds(
        self,
        text_scores: list,
        graph_scores: list,
        labels: list,
        block_thresholds: Optional[list] = None,
    ) -> list:
        """Sweep block thresholds and return list of (threshold, accuracy, precision, recall, f1) tuples.

        Only BLOCK vs ALLOW is compared (ESCALATE counts as not-blocked).
        """
        try:
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
        except ImportError:
            raise ImportError("scikit-learn is required for sweep_thresholds. pip install scikit-learn")

        if block_thresholds is None:
            block_thresholds = [round(t * 0.05, 2) for t in range(1, 21)]

        results = []
        combined = [
            self.alpha * ts + (1.0 - self.alpha) * gs
            for ts, gs in zip(text_scores, graph_scores)
        ]

        for thr in block_thresholds:
            preds = [1 if c >= thr else 0 for c in combined]
            acc = accuracy_score(labels, preds)
            prec = precision_score(labels, preds, zero_division=0)
            rec = recall_score(labels, preds, zero_division=0)
            f1 = f1_score(labels, preds, zero_division=0)
            results.append({
                "block_threshold": thr,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
            })
        return results
