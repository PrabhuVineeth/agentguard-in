#!/usr/bin/env python3
"""Evaluate Component B text guardrails on held-out test split."""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentguard.guardrail.dataset_builder import TextSnippet, extract_guardrail_dataset
from agentguard.guardrail.hf_guard import HFClassifierGuardrail
from agentguard.guardrail.multilingual_guard import MultilingualGuardrail
from agentguard.guardrail.regex_guard import RegexGuardrail


def evaluate_model(name: str, model, test_snippets: List[TextSnippet], threshold: float = 0.5) -> Dict[str, Any]:
    y_true = [s.label for s in test_snippets]
    scores = [model.score(s.text) for s in test_snippets]
    y_pred = [1 if sc >= threshold else 0 for sc in scores]

    tp = sum(1 for p, y in zip(y_pred, y_true) if p == 1 and y == 1)
    fp = sum(1 for p, y in zip(y_pred, y_true) if p == 1 and y == 0)
    tn = sum(1 for p, y in zip(y_pred, y_true) if p == 0 and y == 0)
    fn = sum(1 for p, y in zip(y_pred, y_true) if p == 0 and y == 1)

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    acc = (tp + tn) / len(y_true) if y_true else 0.0

    # Per-language breakdown
    by_lang = {}
    for lang in ["en", "hi", "kn"]:
        l_snips = [s for s in test_snippets if s.language == lang]
        if l_snips:
            l_y = [s.label for s in l_snips]
            l_scores = [model.score(s.text) for s in l_snips]
            l_pred = [1 if sc >= threshold else 0 for sc in l_scores]
            l_tp = sum(1 for p, y in zip(l_pred, l_y) if p == 1 and y == 1)
            l_fp = sum(1 for p, y in zip(l_pred, l_y) if p == 1 and y == 0)
            l_fn = sum(1 for p, y in zip(l_pred, l_y) if p == 0 and y == 1)
            l_prec = l_tp / (l_tp + l_fp) if (l_tp + l_fp) > 0 else 0.0
            l_rec = l_tp / (l_tp + l_fn) if (l_tp + l_fn) > 0 else 0.0
            l_f1 = (2 * l_prec * l_rec) / (l_prec + l_rec) if (l_prec + l_rec) > 0 else 0.0
            by_lang[lang] = {"count": len(l_snips), "precision": l_prec, "recall": l_rec, "f1": l_f1}

    # By attack family on injected snippets
    by_family = {}
    for s, sc, p in zip(test_snippets, scores, y_pred):
        if s.label == 1:
            fam = s.attack_family or "unknown"
            if fam not in by_family:
                by_family[fam] = {"total": 0, "detected": 0}
            by_family[fam]["total"] += 1
            if p == 1:
                by_family[fam]["detected"] += 1

    for fam in by_family:
        tot = by_family[fam]["total"]
        det = by_family[fam]["detected"]
        by_family[fam]["recall"] = det / tot if tot > 0 else 0.0

    # Failure cases for confusion analysis
    false_positives = []
    false_negatives = []
    for s, sc, p in zip(test_snippets, scores, y_pred):
        if p == 1 and s.label == 0:
            false_positives.append((s.text[:80], sc, s.language))
        elif p == 0 and s.label == 1:
            false_negatives.append((s.text[:80], sc, s.language, s.attack_family))

    return {
        "model": name,
        "threshold": threshold,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "by_lang": by_lang,
        "by_family": by_family,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def compute_pr_curve(model, test_snippets: List[TextSnippet]) -> List[Dict[str, float]]:
    y_true = [s.label for s in test_snippets]
    scores = [model.score(s.text) for s in test_snippets]
    curve = []
    for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        y_pred = [1 if sc >= t else 0 for sc in scores]
        tp = sum(1 for p, y in zip(y_pred, y_true) if p == 1 and y == 1)
        fp = sum(1 for p, y in zip(y_pred, y_true) if p == 1 and y == 0)
        fn = sum(1 for p, y in zip(y_pred, y_true) if p == 0 and y == 1)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        curve.append({"threshold": t, "precision": prec, "recall": rec, "f1": f1})
    return curve


def main():
    parser = argparse.ArgumentParser(description="Evaluate Component B Text Guardrails")
    parser.add_argument("--data_dir", type=str, default="data")
    parser.add_argument("--model_dir", type=str, default="data/models/text_guardrail")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    model_dir = Path(args.model_dir)

    all_snippets = extract_guardrail_dataset(data_dir)
    test_snippets = [s for s in all_snippets if s.split == "test"]

    print("=================================================================")
    print("COMPONENT B TEXT GUARDRAIL EVALUATION (HELD-OUT TEST SET)")
    print(f"Test Set Size: {len(test_snippets)} snippets (Clean: {sum(1 for s in test_snippets if s.label == 0)}, Injected: {sum(1 for s in test_snippets if s.label == 1)})")
    print("=================================================================\n")

    models = [
        ("Regex Baseline", RegexGuardrail(), 0.50),
        ("HF Classifier Baseline", HFClassifierGuardrail(), 0.50),
        ("Multilingual Guardrail (Main)", MultilingualGuardrail(model_dir=model_dir), 0.20),
    ]

    results = []
    for name, m, t in models:
        res = evaluate_model(name, m, test_snippets, threshold=t)
        results.append(res)
        print(f"--- Model: {name} (Threshold = {t:.2f}) ---")
        print(f"Accuracy : {res['accuracy'] * 100:.1f}%")
        print(f"Precision: {res['precision'] * 100:.1f}%")
        print(f"Recall   : {res['recall'] * 100:.1f}%")
        print(f"F1 Score : {res['f1'] * 100:.1f}%\n")

        print("  Per-Language Performance:")
        for lang, l_m in sorted(res["by_lang"].items()):
            print(f"    - [{lang.upper()}] (n={l_m['count']}): Precision: {l_m['precision']*100:.1f}%, Recall: {l_m['recall']*100:.1f}%, F1: {l_m['f1']*100:.1f}%")

        print("\n  Detection Rate by Attack Family (Recall):")
        for fam, f_m in sorted(res["by_family"].items()):
            print(f"    - {fam:<25}: {f_m['recall']*100:.1f}% ({f_m['detected']}/{f_m['total']})")
        print("\n" + "-" * 65 + "\n")

    # Main Model PR Curve and Threshold Analysis
    main_model = MultilingualGuardrail(model_dir=model_dir)
    pr_curve = compute_pr_curve(main_model, test_snippets)
    print("THRESHOLD ANALYSIS & PR CURVE (Multilingual Guardrail Main Model):")
    print("| Threshold | Precision | Recall | F1 Score |")
    print("| :--- | :--- | :--- | :--- |")
    for pt in pr_curve:
        print(f"| {pt['threshold']:.1f} | {pt['precision']*100:.1f}% | {pt['recall']*100:.1f}% | {pt['f1']*100:.1f}% |")

    # Confusion Analysis on Main Model
    main_res = results[2]
    print("\n" + "=" * 65)
    print("CONFUSION ANALYSIS OF FAILURE CASES (Multilingual Guardrail)")
    print("=" * 65)
    print(f"False Positives (Clean text incorrectly flagged as attack): {len(main_res['false_positives'])}")
    for txt, sc, lang in main_res['false_positives'][:3]:
        print(f"  - [{lang}] Score: {sc:.3f} | Text: \"{txt}...\"")

    print(f"\nFalse Negatives (Attacks missed by guardrail): {len(main_res['false_negatives'])}")
    for txt, sc, lang, fam in main_res['false_negatives'][:5]:
        print(f"  - [{lang} / {fam}] Score: {sc:.3f} | Text: \"{txt}...\"")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
