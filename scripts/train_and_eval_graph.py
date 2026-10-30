#!/usr/bin/env python3
"""Train, ablate, and evaluate Component C Graph Trajectory Detectors (GNN & Baseline)."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentguard.eval.harness import EvaluationHarness
from agentguard.graph.feature_baseline import GraphFeatureBaseline
from agentguard.graph.gnn_detector import GNNDetector
from agentguard.graph.trajectory_graph import TrajectoryGraph
from agentguard.logging.jsonl_logger import TrajectoryLogger


def main():
    parser = argparse.ArgumentParser(description="Train and Evaluate Component C Graph Trajectory Detectors")
    parser.add_argument("--log_file", type=str, default="data/runs/scaled_benchmark_runs.jsonl")
    parser.add_argument("--model_dir", type=str, default="data/models/graph_detector")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    log_path = Path(args.log_file)
    model_dir = Path(args.model_dir)

    print("=================================================================")
    print("COMPONENT C: GRAPH DETECTOR TRAINING & ABLATION STUDY")
    print(f"Trajectory Source: {log_path} | Models Target: {model_dir}")
    print("=================================================================")

    # 1. Load runs and convert to graphs
    logger = TrajectoryLogger(log_path)
    runs = logger.read_runs()
    print(f"Loaded {len(runs)} trajectory runs.")

    graphs: List[TrajectoryGraph] = [TrajectoryGraph(r) for r in runs]
    train_graphs = [g for g in graphs if g.split == "train"]
    val_graphs = [g for g in graphs if g.split == "val"]
    test_graphs = [g for g in graphs if g.split == "test"]

    print(f"Graph Partitions:")
    print(f"  - Train: {len(train_graphs)} graphs (Clean: {sum(1 for g in train_graphs if not g.is_attacked)}, Attacked: {sum(1 for g in train_graphs if g.is_attacked)})")
    print(f"  - Val  : {len(val_graphs)} graphs (Clean: {sum(1 for g in val_graphs if not g.is_attacked)}, Attacked: {sum(1 for g in val_graphs if g.is_attacked)})")
    print(f"  - Test : {len(test_graphs)} graphs (Clean: {sum(1 for g in test_graphs if not g.is_attacked)}, Attacked: {sum(1 for g in test_graphs if g.is_attacked)})")

    train_labels = [1 if g.is_attacked else 0 for g in train_graphs]
    test_labels = [1 if g.is_attacked else 0 for g in test_graphs]

    # Models & Ablation configurations
    model_results = {}

    # -------------------------------------------------------------
    # 1. Baseline: Gradient Boosting (with untrusted flag)
    # -------------------------------------------------------------
    print("\n[1/5] Training Gradient Boosting Baseline (Full features)...")
    base_full = GraphFeatureBaseline(include_untrusted_flag=True)
    base_full.train(train_graphs, train_labels)
    base_full.save(model_dir / "baseline_full")
    test_scores_bf = [base_full.score(g) for g in test_graphs]
    res_bf = EvaluationHarness.evaluate_binary_predictions(test_labels, test_scores_bf, threshold=0.50)
    model_results["Gradient Boosting (Full)"] = res_bf

    # -------------------------------------------------------------
    # 2. Baseline Ablation: Gradient Boosting (without untrusted flag)
    # -------------------------------------------------------------
    print("[2/5] Training Gradient Boosting Baseline (Ablated: No Untrusted Flag)...")
    base_ablated = GraphFeatureBaseline(include_untrusted_flag=False)
    base_ablated.train(train_graphs, train_labels)
    base_ablated.save(model_dir / "baseline_ablated")
    test_scores_ba = [base_ablated.score(g) for g in test_graphs]
    res_ba = EvaluationHarness.evaluate_binary_predictions(test_labels, test_scores_ba, threshold=0.50)
    model_results["Gradient Boosting (No Untrusted Flag)"] = res_ba

    # -------------------------------------------------------------
    # 3. Main GNN: GraphSAGE (with untrusted flag)
    # -------------------------------------------------------------
    print(f"[3/5] Training GraphSAGE GNN (Full features, {args.epochs} epochs)...")
    gnn_sage = GNNDetector(model_type="graphsage", include_untrusted_flag=True)
    gnn_sage.train(train_graphs, val_graphs, epochs=args.epochs)
    gnn_sage.save(model_dir / "graphsage_full")
    test_scores_sage = [gnn_sage.score(g) for g in test_graphs]
    res_sage = EvaluationHarness.evaluate_binary_predictions(test_labels, test_scores_sage, threshold=0.50)
    model_results["GraphSAGE GNN (Full)"] = res_sage

    # -------------------------------------------------------------
    # 4. GNN Ablation: GraphSAGE (without untrusted flag)
    # -------------------------------------------------------------
    print(f"[4/5] Training GraphSAGE GNN (Ablated: No Untrusted Flag, {args.epochs} epochs)...")
    gnn_sage_ablated = GNNDetector(model_type="graphsage", include_untrusted_flag=False)
    gnn_sage_ablated.train(train_graphs, val_graphs, epochs=args.epochs)
    gnn_sage_ablated.save(model_dir / "graphsage_ablated")
    test_scores_sage_ab = [gnn_sage_ablated.score(g) for g in test_graphs]
    res_sage_ab = EvaluationHarness.evaluate_binary_predictions(test_labels, test_scores_sage_ab, threshold=0.50)
    model_results["GraphSAGE GNN (No Untrusted Flag)"] = res_sage_ab

    # -------------------------------------------------------------
    # 5. Comparative GNN: GAT (Graph Attention Network)
    # -------------------------------------------------------------
    print(f"[5/5] Training GAT GNN (Full features, {args.epochs} epochs)...")
    gnn_gat = GNNDetector(model_type="gat", include_untrusted_flag=True)
    gnn_gat.train(train_graphs, val_graphs, epochs=args.epochs)
    gnn_gat.save(model_dir / "gat_full")
    test_scores_gat = [gnn_gat.score(g) for g in test_graphs]
    res_gat = EvaluationHarness.evaluate_binary_predictions(test_labels, test_scores_gat, threshold=0.50)
    model_results["GAT GNN (Full)"] = res_gat

    # Print Comparative Results Table with 95% Bootstrap CIs
    print("\n" + "=" * 80)
    print("COMPONENT C ABLATION STUDY & MODEL COMPARISON (HELD-OUT TEST SET)")
    print("=" * 80)
    print(f"{'Model Architecture':<36} | {'Accuracy':<16} | {'Precision':<16} | {'Recall':<16} | {'F1 Score':<16}")
    print("-" * 80)
    for name, res in model_results.items():
        acc = res["accuracy"].format_str()
        prec = res["precision"].format_str()
        rec = res["recall"].format_str()
        f1 = res["f1"].format_str()
        print(f"{name:<36} | {acc:<16} | {prec:<16} | {rec:<16} | {f1:<16}")

    print("=" * 80)

    # Print LaTeX Table
    print("\nLATEX CODE (IEEE FORMAT):\n")
    print(EvaluationHarness.generate_latex_table(model_results))
    print("\n")


if __name__ == "__main__":
    main()
