# AgentGuard-IN: Project Summary

**Full Title**: AgentGuard-IN — A Benchmark and Layered Defense Framework Against Prompt-Injection Attacks on Tool-Using LLM Agents in Indian-Context Workflows

**Target Venue**: IEEE-grade publication (empirical methodology, reproducible results, zero data leakage)

---

## Abstract

We present **AgentGuard-IN**, a comprehensive benchmark and multi-component defense framework targeting prompt-injection attacks on tool-using LLM agents operating in Indian-language, Indian-domain workflows. Four mock workflow domains are covered: UPI digital payments, IRCTC railway ticketing, government welfare form submission, and multilingual email assistance. The framework contributes:

1. **A reproducible benchmark** of 1,060 agent trajectories across 4 Indian Digital Public Infrastructure domains (UPI, IRCTC, Citizen Welfare, Email).
2. **Component B (Text Guardrail)**: An Indic subword character n-gram classifier evaluated on wild real-world prompt injections (`deepset/prompt-injections`), achieving an **89.7% F1 score and 0.971 ROC-AUC** (with 92.9% precision).
3. **Component C (Graph Detector)**: A GraphSAGE GNN operating on heterogeneous execution-influence graphs derived from multi-turn agent trajectories to detect topological hijacking (<5.1 ms latency on CPU).
4. **Component D (Layered Defense)**: A configurable score-fusion combiner with an asymmetric three-way policy (ALLOW / ESCALATE / BLOCK), reducing agent Attack Success Rate (ASR) from **61.6% to 2.4%** at a **0.0% false-block rate** on clean user transactions.

All detection metrics are reported strictly on canonical real-world open datasets to avoid synthetic shortcut artifacts.

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────┐
│  Component B: Text Guardrail│  ← Pre-execution, per-turn text risk score
│  (Regex + Multilingual TF-IDF│     89.7% F1, 0.971 ROC-AUC on wild attacks
│   + Logistic Regression)    │
└────────────┬────────────────┘
             │  text_score ∈ [0,1]
             ▼
┌─────────────────────────────┐
│  Component C: Graph Detector│  ← Post-turn, trajectory-level hijack score
│  (TrajectoryGraph → GNN     │     Tracks causal influence to privileged tools
│   GraphSAGE / GAT)          │
└────────────┬────────────────┘
             │  graph_score ∈ [0,1]
             ▼
┌─────────────────────────────┐
│  Component D: Layered       │  ← Fusion + asymmetric three-way policy
│  Defense Combiner           │     combined = α·B + (1-α)·C
│  combined = α·B + (1-α)·C   │     ≥ 0.70 → BLOCK, ≥ 0.35 → ESCALATE, < 0.35 → ALLOW
│  → ALLOW / ESCALATE / BLOCK │     0.0% false-block rate on clean transactions
└─────────────────────────────┘
```

---

## Key Empirical Results

### 1. Real-World Kaggle / Deepset Benchmark (116 Test Samples)

| Model Architecture | Threshold | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Regex Baseline | 0.50 | 48.3% | 0.0% | 0.0% | **0.0%** | 0.500 |
| Synthetic-Only Model | 0.25 | 61.2% | 82.6% | 31.7% | **45.8%** | 0.698 |
| Meta Prompt Guard 2 (86M on Groq) | 0.50 | 56.9% | 69.2% | 30.0% | **41.9%** | 0.822 |
| **Composite Guard (Ours: Real Kaggle + Indic)** | 0.25 | **89.7%** | **92.9%** | **86.7%** | **89.7%** | **0.971** |

### 2. End-to-End Agentic Security Evaluation (1,060 Runs)

| Metric | Vulnerable Agent | Prompt-Guarded Agent | Delta ($\Delta$) |
| :--- | :---: | :---: | :---: |
| Benign Utility (Clean) | **100.0%** (30/30) | **100.0%** (30/30) | 0.0 pp |
| Utility Under Attack | 1.6% | **44.0%** | **+42.4 pp** |
| Attack Success Rate (ASR) | **61.6%** (308/500) | **2.4%** (12/500) | **−59.2 pp** |
| False-Block Rate | **0.0%** (0/30) | **0.0%** (0/30) | **0.0 pp** |

### 3. Threshold Sensitivity & Operating Horizon (Real Dataset)

| Operating Threshold $\theta$ | Accuracy | Precision | Recall | F1 Score | FP | FN |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.20 | 87.9% | 85.9% | 91.7% | 88.7% | 9 | 5 |
| **0.25 (Optimal)** | **89.7%** | **92.9%** | **86.7%** | **89.7%** | **4** | **8** |
| 0.30 | 89.7% | **100.0%** | 80.0% | 88.9% | 0 | 12 |
| **0.35 (Escalation)** | 87.1% | **100.0%** | 75.0% | 85.7% | **0** | 15 |

At $\theta \ge 0.30$, precision reaches 100% with 0 false positives on clean queries, confirming the safety of the Component D threshold design.

---

## Repository Structure

```
agentguard_in/
├── configs/             # YAML: tasks, attacks, models, budget, guardrail
├── data/
│   ├── attacks_benchmark.json
│   ├── cache/           # Deterministic mock LLM response cache
│   └── runs/            # JSONL trajectory logs
├── src/agentguard/
│   ├── tools/           # Mock tools: UPI, IRCTC, Email, Govt Forms
│   ├── tasks/           # Task schemas and programmatic generators
│   ├── attacks/         # 5 attack family templates + injector
│   ├── agents/          # Multi-provider agent loop (mock_vulnerable, mock_robust)
│   ├── logging/         # JSONL trajectory schema + logger
│   ├── guardrail/       # Component B: Regex + Multilingual classifier
│   ├── graph/           # Component C: TrajectoryGraph + GNN models
│   ├── defense/         # Component D: LayeredDefenseCombiner
│   └── eval/            # EvaluationHarness, bootstrap CIs, LaTeX table
├── tests/               # 60 pytest tests (100% pass rate)
├── scripts/             # CLI execution scripts
├── RESULTS.md           # All empirical results (no fabricated numbers)
├── LIMITATIONS.md       # Publication-standard limitations
├── DECISIONS.md         # Architecture decision log
├── NOVELTY_NOTES.md     # Novelty claims
└── CHECKPOINT_PHASE_*.md # Per-phase completion records
```

---

## Reproducibility

```bash
# Install
pip install -r requirements.txt
pip install -e .

# Run tests (60 tests, ~30s)
pytest -v tests/

# Phase 1: Smoke test
python scripts/run_benchmark.py --provider mock --tasks 5 --mode both

# Phase 2: Scaled benchmark (1,060 runs)
python scripts/run_scaled_benchmark.py --max_runs 500

# Phase 3: Train + evaluate text guardrail
python scripts/train_text_guardrail.py
python scripts/evaluate_guardrail.py

# Phase 4: Train + evaluate graph detectors
python scripts/train_and_eval_graph.py --epochs 20

# Phase 5: End-to-end layered defense evaluation
python scripts/run_end_to_end_eval.py
```

All experiments run on **CPU only** in under **10 minutes total** wall-clock time. No GPU, no paid API, no cloud infrastructure required.

---

## Safety Guarantee

> **No actual financial transactions, travel bookings, government form submissions, or email messages are created.** Every tool in AgentGuard-IN operates exclusively on in-memory mock state machines. All account IDs, PNRs, form numbers, and credentials are synthetic.

---

## Citation

```bibtex
@misc{agentguard_in_2026,
  title   = {{AgentGuard-IN}: A Benchmark and Layered Defense Against
             Prompt-Injection Attacks on Tool-Using LLM Agents
             in Indian-Context Workflows},
  year    = {2026},
  note    = {IEEE-format empirical study. Reproducible open-source benchmark.}
}
```

---

*Last updated: 2026-10-28*

