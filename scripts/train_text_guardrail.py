#!/usr/bin/env python3
"""Train and save Component B Multilingual Text Guardrail."""

import argparse
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentguard.guardrail.dataset_builder import extract_guardrail_dataset
from agentguard.guardrail.multilingual_guard import MultilingualGuardrail


def main():
    parser = argparse.ArgumentParser(description="Train Multilingual Text Guardrail")
    parser.add_argument("--data_dir", type=str, default="data", help="Data directory containing task JSONs")
    parser.add_argument("--output_dir", type=str, default="data/models/text_guardrail", help="Directory to save model")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    print("=================================================================")
    print("TRAINING COMPONENT B MULTILINGUAL TEXT GUARDRAIL")
    print(f"Data Source: {data_dir} | Target Output: {output_dir}")
    print("=================================================================")

    # 1. Extract snippets
    all_snippets = extract_guardrail_dataset(data_dir)
    train_snippets = [s for s in all_snippets if s.split == "train"]
    val_snippets = [s for s in all_snippets if s.split == "val"]

    print(f"Total Extracted Snippets: {len(all_snippets)}")
    print(f"  - Train Partition: {len(train_snippets)} (Clean: {sum(1 for s in train_snippets if s.label == 0)}, Injected: {sum(1 for s in train_snippets if s.label == 1)})")
    print(f"  - Val Partition  : {len(val_snippets)} (Clean: {sum(1 for s in val_snippets if s.label == 0)}, Injected: {sum(1 for s in val_snippets if s.label == 1)})")

    train_texts = [s.text for s in train_snippets]
    train_labels = [s.label for s in train_snippets]
    val_texts = [s.text for s in val_snippets]
    val_labels = [s.label for s in val_snippets]

    # Include real-world Kaggle/Deepset benchmark if present
    real_train_csv = data_dir / "real_benchmark" / "train.csv"
    if real_train_csv.exists():
        import pandas as pd
        df_real = pd.read_csv(real_train_csv)
        print(f"  - Real-World Kaggle Train: {len(df_real)} samples added to training")
        train_texts.extend(df_real["text"].tolist())
        train_labels.extend(df_real["label"].tolist())

    # 2. Train model
    guardrail = MultilingualGuardrail()
    guardrail.train(
        texts=train_texts,
        labels=train_labels,
        val_texts=val_texts,
        val_labels=val_labels,
    )

    # 3. Save model
    guardrail.save(output_dir)
    print(f"\nModel successfully saved to {output_dir.resolve()}")
    print(f"Calibrated Optimal Threshold: {guardrail.optimal_threshold:.2f}")
    print("Retrain Command: python scripts/train_text_guardrail.py")


if __name__ == "__main__":
    main()
