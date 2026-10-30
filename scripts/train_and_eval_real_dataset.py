#!/usr/bin/env python3
"""Train and evaluate text guardrails on real-world Kaggle/Deepset Prompt Injection dataset."""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentguard.guardrail.dataset_builder import extract_guardrail_dataset
from agentguard.guardrail.groq_guard import GroqPromptGuardrail
from agentguard.guardrail.multilingual_guard import MultilingualGuardrail
from agentguard.guardrail.regex_guard import RegexGuardrail


def evaluate_model_on_data(name: str, model, texts: List[str], y_true: List[int], threshold: float = 0.5) -> Dict[str, Any]:
    t0 = time.time()
    scores = [model.score(t) for t in texts]
    elapsed = time.time() - t0
    avg_latency_ms = (elapsed / len(texts)) * 1000 if texts else 0.0

    y_pred = [1 if s >= threshold else 0 for s in scores]
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, scores)
    except Exception:
        auc = 0.5

    return {
        "model": name,
        "threshold": threshold,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": auc,
        "latency_ms": avg_latency_ms,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Guardrails on Real-World Kaggle/Deepset Dataset")
    parser.add_argument("--real_data_dir", default="data/real_benchmark")
    parser.add_argument("--agent_data_dir", default="data")
    parser.add_argument("--output_model_dir", default="data/models/text_guardrail_real")
    parser.add_argument("--eval_groq", action="store_true", default=True, help="Evaluate Groq Prompt Guard 2")
    args = parser.parse_args()

    real_dir = Path(args.real_data_dir)
    train_csv = real_dir / "train.csv"
    test_csv = real_dir / "test.csv"

    if not train_csv.exists() or not test_csv.exists():
        print(f"Error: Real benchmark CSVs not found in {real_dir}")
        sys.exit(1)

    print("=================================================================")
    print("REAL-WORLD KAGGLE / DEEPSET PROMPT INJECTION BENCHMARK EVALUATION")
    print(f"Source: {real_dir}")
    print("=================================================================")

    df_train_real = pd.read_csv(train_csv)
    df_test_real = pd.read_csv(test_csv)

    print(f"Loaded Real Dataset:")
    print(f"  - Train: {len(df_train_real)} samples (Clean: {sum(df_train_real['label']==0)}, Injection: {sum(df_train_real['label']==1)})")
    print(f"  - Test : {len(df_test_real)} samples (Clean: {sum(df_test_real['label']==0)}, Injection: {sum(df_test_real['label']==1)})")

    # Load agentguard synthetic data for composite training
    agent_snippets = extract_guardrail_dataset(Path(args.agent_data_dir))
    agent_train = [s for s in agent_snippets if s.split == "train"]
    print(f"Loaded Indic AgentGuard Dataset:")
    print(f"  - Train: {len(agent_train)} samples")

    test_texts = df_test_real["text"].tolist()
    test_labels = df_test_real["label"].tolist()

    results = []

    # 1. Regex Baseline
    print("\n[1/4] Evaluating Regex Baseline...")
    regex = RegexGuardrail()
    res_regex = evaluate_model_on_data("Regex Baseline", regex, test_texts, test_labels, threshold=0.50)
    results.append(res_regex)

    # 2. Existing Synthetic-Only Model
    print("[2/4] Evaluating Model 1: Trained ONLY on Synthetic Indic Data...")
    existing_guard = MultilingualGuardrail(Path("data/models/text_guardrail"))
    res_existing = evaluate_model_on_data("Synthetic-Only Guard", existing_guard, test_texts, test_labels, threshold=0.25)
    results.append(res_existing)

    # 3. Composite-Trained Model (Real Kaggle + Indic)
    print("[3/4] Training & Evaluating Model 2: Composite (Real Kaggle + Indic Data)...")
    comp_train_texts = df_train_real["text"].tolist() + [s.text for s in agent_train]
    comp_train_labels = df_train_real["label"].tolist() + [s.label for s in agent_train]
    composite_guard = MultilingualGuardrail()
    composite_guard.train(comp_train_texts, comp_train_labels)
    composite_guard.save(Path(args.output_model_dir))
    res_composite = evaluate_model_on_data("Composite Guard (Real+Indic)", composite_guard, test_texts, test_labels, threshold=0.25)
    results.append(res_composite)

    # 4. Meta Prompt Guard 2 (via Groq API)
    if args.eval_groq:
        try:
            print("[4/4] Evaluating Model 3: Meta Prompt Guard 2 (86M) on Groq LPU...")
            groq_guard = GroqPromptGuardrail()
            res_groq = evaluate_model_on_data("Meta Prompt Guard 2 (Groq)", groq_guard, test_texts, test_labels, threshold=0.50)
            results.append(res_groq)
        except Exception as e:
            print(f"Groq evaluation skipped due to: {e}")

    # Print Comparative Results Table
    print("\n" + "=" * 95)
    print("REAL-WORLD BENCHMARK EVALUATION RESULTS (HELD-OUT TEST SET — 116 SAMPLES)")
    print("=" * 95)
    header = f"{'Model':<30} | {'Threshold':<9} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'ROC-AUC':<8} | {'Latency':<8}"
    print(header)
    print("-" * 95)
    for r in results:
        m_name = r["model"]
        th = f"{r['threshold']:.2f}"
        acc = f"{r['accuracy']*100:.1f}%"
        pr = f"{r['precision']*100:.1f}%"
        rc = f"{r['recall']*100:.1f}%"
        f1 = f"{r['f1']*100:.1f}%"
        auc = f"{r['roc_auc']:.3f}"
        lat = f"{r['latency_ms']:.1f}ms"
        print(f"{m_name:<30} | {th:<9} | {acc:<10} | {pr:<10} | {rc:<10} | {f1:<10} | {auc:<8} | {lat:<8}")
    print("=" * 95)

    # Generate Markdown Table for Results.md
    print("\n### Real-World Evaluation Markdown Table:")
    md_lines = [
        "| Model | Threshold | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Latency |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in results:
        md_lines.append(
            f"| **{r['model']}** | {r['threshold']:.2f} | {r['accuracy']*100:.1f}% | {r['precision']*100:.1f}% | {r['recall']*100:.1f}% | **{r['f1']*100:.1f}%** | {r['roc_auc']:.3f} | {r['latency_ms']:.1f}ms |"
        )
    print("\n".join(md_lines))


if __name__ == "__main__":
    main()

