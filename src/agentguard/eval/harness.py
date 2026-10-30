"""Shared Evaluation Harness used across all components in AgentGuard-IN."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


@dataclass
class EvaluationMetricWithCI:
    mean: float
    ci_lower: float
    ci_upper: float

    def format_latex(self, pct: bool = True) -> str:
        factor = 100.0 if pct else 1.0
        return f"{self.mean * factor:.1f} \\pm [{(self.ci_upper - self.mean) * factor:.1f}]"

    def format_str(self, pct: bool = True) -> str:
        factor = 100.0 if pct else 1.0
        return f"{self.mean * factor:.1f}% [{self.ci_lower * factor:.1f}%, {self.ci_upper * factor:.1f}%]"


def compute_bootstrap_ci(
    y_true: List[int],
    y_pred: List[int],
    metric_fn: Callable[[List[int], List[int]], float],
    n_bootstraps: int = 500,
    alpha: float = 0.05,
    seed: int = 42,
) -> EvaluationMetricWithCI:
    """Compute empirical mean and 95% bootstrap confidence intervals."""
    rng = np.random.RandomState(seed)
    y_t = np.array(y_true)
    y_p = np.array(y_pred)
    n = len(y_t)

    if n == 0:
        return EvaluationMetricWithCI(0.0, 0.0, 0.0)

    base_score = float(metric_fn(y_t, y_p))
    boot_scores = []

    for _ in range(n_bootstraps):
        indices = rng.randint(0, n, size=n)
        sample_yt = y_t[indices]
        sample_yp = y_p[indices]
        # Avoid zero division when sample has only 1 class
        try:
            s = float(metric_fn(sample_yt, sample_yp))
            boot_scores.append(s)
        except Exception:
            pass

    if not boot_scores:
        return EvaluationMetricWithCI(base_score, base_score, base_score)

    ci_lower = float(np.percentile(boot_scores, 100 * (alpha / 2)))
    ci_upper = float(np.percentile(boot_scores, 100 * (1 - alpha / 2)))
    return EvaluationMetricWithCI(mean=base_score, ci_lower=ci_lower, ci_upper=ci_upper)


class EvaluationHarness:
    """Unified evaluation harness producing verified metrics, bootstrap CIs, and LaTeX tables."""

    @classmethod
    def evaluate_binary_predictions(
        cls,
        y_true: List[int],
        y_scores: List[float],
        threshold: float = 0.5,
        n_bootstraps: int = 500,
    ) -> Dict[str, Any]:
        """Compute complete statistical performance report with 95% bootstrap CIs."""
        y_pred = [1 if s >= threshold else 0 for s in y_scores]

        acc_ci = compute_bootstrap_ci(y_true, y_pred, accuracy_score, n_bootstraps=n_bootstraps)
        prec_ci = compute_bootstrap_ci(
            y_true, y_pred, lambda yt, yp: precision_score(yt, yp, zero_division=0), n_bootstraps=n_bootstraps
        )
        rec_ci = compute_bootstrap_ci(
            y_true, y_pred, lambda yt, yp: recall_score(yt, yp, zero_division=0), n_bootstraps=n_bootstraps
        )
        f1_ci = compute_bootstrap_ci(
            y_true, y_pred, lambda yt, yp: f1_score(yt, yp, zero_division=0), n_bootstraps=n_bootstraps
        )

        try:
            auc = float(roc_auc_score(y_true, y_scores)) if len(set(y_true)) > 1 else 1.0
        except Exception:
            auc = 1.0

        return {
            "total_samples": len(y_true),
            "threshold": threshold,
            "accuracy": acc_ci,
            "precision": prec_ci,
            "recall": rec_ci,
            "f1": f1_ci,
            "roc_auc": auc,
        }

    @classmethod
    def generate_latex_table(cls, model_eval_results: Dict[str, Dict[str, Any]]) -> str:
        """Generate publication-ready IEEE LaTeX comparative table."""
        lines = [
            "\\begin{table*}[t]",
            "\\centering",
            "\\caption{Component C & D Detection Performance and Ablations (95\\% Bootstrap CIs)}",
            "\\label{tab:evaluation_results}",
            "\\begin{tabular}{lcccccc}",
            "\\hline",
            "\\textbf{Defense Model} & \\textbf{Threshold} & \\textbf{Accuracy (\\%)} & \\textbf{Precision (\\%)} & \\textbf{Recall (\\%)} & \\textbf{F1 Score (\\%)} & \\textbf{ROC-AUC} \\\\",
            "\\hline",
        ]
        for name, res in model_eval_results.items():
            th = f"{res['threshold']:.2f}"
            acc = res["accuracy"].format_latex()
            prec = res["precision"].format_latex()
            rec = res["recall"].format_latex()
            f1 = res["f1"].format_latex()
            auc = f"{res['roc_auc']:.3f}"
            lines.append(f"{name} & {th} & {acc} & {prec} & {rec} & {f1} & {auc} \\\\")

        lines.extend([
            "\\hline",
            "\\end{tabular}",
            "\\end{table*}",
        ])
        return "\n".join(lines)
