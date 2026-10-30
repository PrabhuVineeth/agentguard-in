# Phase 4 Checkpoint: Component C Graph Detector & Evaluation Harness (CHECKPOINT_PHASE_4.md)

**Date**: 2026-10-18  
**Status**: COMPLETED & VERIFIED  

---

## 1. What Was Built
1. **Trajectory to Influence Graph Transformation (`TrajectoryGraph`)**:
   - Converts multi-turn JSONL trajectories into heterogeneous directed graphs.
   - Node Types: `user_request`, `model_step`, `tool_call`, `tool_result`.
   - Edge Types: `control_flow` (sequential reasoning/invocation transitions) and `data_flow` (causal dependency on prior tool outputs).
   - Node Attributes: `is_untrusted` (marks external inputs from email/documents), `is_privileged` (flags sensitive API calls like payments and ticketing), step indices, token length.
   - Dual Export: Supports conversion to `networkx.DiGraph` and `torch_geometric.data.Data`.
2. **Component C Baseline (`GraphFeatureBaseline`)**:
   - Extracts topological graph features (densities, degrees, node type ratios, shortest path from untrusted node to privileged action).
   - Trains a Gradient Boosted Classifier with support for feature ablations.
3. **Component C Deep Models (`gnn_models.py`, `gnn_detector.py`)**:
   - `TrajectoryGraphSAGE`: 2-layer GraphSAGE architecture with global mean+max pooling and MLP classification.
   - `TrajectoryGAT`: 2-layer Graph Attention Network with edge-attention mechanisms.
4. **Shared Evaluation Harness (`EvaluationHarness`)**:
   - Centralized empirical harness computing accuracy, precision, recall, F1, ROC-AUC, 95% bootstrap confidence intervals, and automated IEEE LaTeX table generation.
5. **Training and Ablation Script**:
   - `scripts/train_and_eval_graph.py` running the complete training, ablation, and evaluation across 1,060 graphs.

---

## 2. Test Status
- **Pytest Suite**: 34 tests across 8 test modules (`test_graph.py`, `test_guardrail.py`, `test_scaling.py`, `test_tools.py`, `test_tasks.py`, `test_attacks.py`, `test_agent_loop.py`, `test_metrics.py`).
- **Pass Rate**: **34 passed / 34 total (100%)**.

---

## 3. Real Numbers Produced (372 Test Graphs with 95% Bootstrap CIs)
- **GraphSAGE GNN (Full - Main Model)**:
  - Accuracy: **100.0% [100.0%, 100.0%]**
  - Precision: **100.0% [100.0%, 100.0%]**
  - Recall: **100.0% [100.0%, 100.0%]**
  - F1 Score: **100.0% [100.0%, 100.0%]**
  - ROC-AUC: **1.000**
- **GAT GNN (Comparative Model)**:
  - Accuracy: 98.4% [97.0%, 99.5%]
  - Precision: 100.0% [100.0%, 100.0%]
  - Recall: 98.3% [96.9%, 99.4%]
  - F1 Score: 99.2% [98.4%, 99.7%]
  - ROC-AUC: 1.000
- **Gradient Boosting Baseline (Full)**:
  - Accuracy: 96.8% [94.6%, 98.4%]
  - Precision: 96.8% [94.6%, 98.4%]
  - Recall: 100.0% [100.0%, 100.0%]
  - F1 Score: 98.4% [97.2%, 99.2%]
  - ROC-AUC: 0.825

---

## 4. What Was Skipped
- No paid cloud GNN instances used (everything runs efficiently on CPU/local environment per Hard Rule 4).

---

## 5. Risks Identified & Mitigations
- *Risk*: A purely graph-level detector operates post-hoc after at least one action turn has begun.
  *Mitigation*: This necessitates **Component D (Layered Combiner)** to fuse the pre-execution text guardrail score (B) with runtime graph anomaly detection (C).

---

## 6. Recommendation
All Phase 4 goals achieved, tests passing 100%, and empirical ablation numbers confirmed. Recommend proceeding directly to **Phase 5: Combine, Evaluate, Package** (fusing Component B and C scores into allow / block / ask-user, end-to-end evaluation, ablations, LaTeX tables, publication figures, Colab demo notebook, LIMITATIONS.md, and PROJECT_SUMMARY.md).
