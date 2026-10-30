# AgentGuard-IN: Dual-Modality Guardrails for Tool-Using AI Agents Against Indirect Prompt Injection

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-63%2F63%20passed%20(100%25)-brightgreen.svg)](tests/)
[![Paper](https://img.shields.io/badge/Paper-IEEE_Conference-red.svg)](paper/main.tex)
[![Dataset](https://img.shields.io/badge/Benchmark-Kaggle%20%2F%20Deepset%20Real-orange.svg)](data/real_benchmark/)

**AgentGuard-IN** is the first reproducible benchmark and model-agnostic layered defense framework specifically designed to protect autonomous tool-using Large Language Model (LLM) agents against **Indirect Prompt Injection (IPI)** in regional **Digital Public Infrastructure (DPI)** ecosystems.

The framework models high-stakes Indian digital workflows—**UPI peer-to-peer payments, IRCTC railway reservation, and citizen welfare subsidy portals**—across English, Hindi (Devanagari script), and Kannada (Dravidian script), and introduces a dual-modality defense uniting pre-execution subword text screening with runtime causal trajectory graph anomaly detection (GraphSAGE).

---

## Key Results at a Glance

| Evaluation Surface | Baseline (Undefended) | AgentGuard-IN (Guarded) | Improvement / Metric |
| :--- | :---: | :---: | :--- |
| **Real-World Wild Injection Detection** | 45.8% F1 (Synthetic-Only) | **89.7% F1 / 0.971 ROC-AUC** | **+43.9 pp** on wild attacks (`deepset/prompt-injections`) |
| **Real-World Precision** | 82.6% | **92.9%** (100% at $\theta \ge 0.30$) | Clean queries correctly admitted without alarms |
| **Agent Tool Hijacking (ASR)** | 61.6% (308 / 500) | **2.4%** (12 / 500) | **$-$59.2 pp reduction** in unauthorized privileged calls |
| **Clean Transaction False-Block Rate** | 0.0% | **0.0%** (0 / 30) | **Zero operational disruption** on legitimate user actions |
| **End-to-End Pipeline Latency** | — | **<8.4 ms** (3.2ms Text + 5.1ms Graph) | **<1%** of standard LLM generation time (CPU-only) |

> **Scientific Grounding & Avoiding Synthetic Shortcuts**:
> Prior synthetic benchmarks frequently report artificially inflated "100% F1" and "1.000 ROC-AUC" metrics due to rigid template distributions and extreme class imbalance. As demonstrated below, models trained solely on synthetic templates suffer severe **shortcut learning**, collapsing to **45.8% F1** on wild attacks. To eliminate misleading evaluation, AgentGuard-IN evaluates strictly on the canonical open benchmark `deepset/prompt-injections` and deterministic agentic state machines.

---

## Defense Architecture

```
Incoming Step (User Goal + Retrieved Tool Observation)
                    │
                    ▼  ── Stage 1: Dual-Source Ingestion ──────────────────────
            ┌───────────────────────────────┐
            │ Ingestion & Taint Tracking   │  Track origin metadata (u_v ∈ {0, 1})
            │ Script Normalization (UTF-8)  │  Preserve raw semantics for agent
            └───────────────┬───────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
 ── Stage 2: Pre-Execution ──         ── Stage 3: Runtime Trajectory ──
┌───────────────────────────────┐     ┌────────────────────────────────┐
│ Component B: Text Guardrail   │     │ Component C: Graph Detector    │
│ Subword Char 3-5 n-grams      │     │ Directed Multigraph G = (V, E) │
│ MaxEnt Classifier (3.2 ms)    │     │ 2-Layer GraphSAGE GNN (5.1 ms) │
│ Groq LPU Meta Prompt Guard 2  │     │ Tracks untrusted → priv flows  │
└───────────────┬───────────────┘     └────────────────┬───────────────┘
                │ s_text ∈ [0, 1]                      │ s_graph ∈ [0, 1]
                └──────────────────┬───────────────────┘
                                   │
                                   ▼  ── Stage 4: Convex Fusion & Triage ─────
                    ┌───────────────────────────────┐
                    │ Component D: Layered Combiner │  s_comb = α·s_text + (1-α)·s_graph
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    s_comb < 0.35             0.35 ≤ s_comb < 0.70       s_comb ≥ 0.70
     [ ALLOW ]                 [ ESCALATE ]               [ BLOCK ]
  Autonomous tool dispatch   Step-up Human OTP/MPIN    Immediate session abort
```

A publication-grade vector architecture diagram is provided in [`paper/figures/methodology.pdf`](paper/figures/methodology.pdf) (and [`paper/figures/methodology.png`](paper/figures/methodology.png)).

---

## Empirical Benchmark Results

### 1. Real-World Kaggle / Deepset Benchmark (116 Held-Out Samples)

Evaluated against the canonical real-world open benchmark `deepset/prompt-injections` (56 benign queries, 60 wild adversarial prompt injections and jailbreaks):

| Model Architecture | Threshold | Accuracy | Precision | Recall | F1 Score | ROC-AUC | CPU Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Regex Heuristic Baseline** | 0.50 | 48.3% | 0.0% | 0.0% | **0.0%** | 0.500 | 0.1 ms |
| **Synthetic-Only Model** *(Trained on Indic Mock)* | 0.25 | 61.2% | 82.6% | 31.7% | **45.8%** | 0.698 | 3.0 ms |
| **Meta Prompt Guard 2** *(86M via Groq LPU)* | 0.50 | 56.9% | 69.2% | 30.0% | **41.9%** | 0.822 | ~150 ms (Cloud) |
| **Composite Guard (Ours: Real Kaggle + Indic)** | 0.25 | **89.7%** | **92.9%** | **86.7%** | **89.7%** | **0.971** | **4.0 ms** |

### 2. Operating Threshold Sensitivity & Confusion Matrix (Real Dataset)

| Operating Threshold $\theta$ | Accuracy | Precision | Recall | F1 Score | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.15 | 78.4% | 71.1% | **98.3%** | 82.5% | 59 | 24 | 32 | 1 |
| 0.20 | 87.9% | 85.9% | 91.7% | 88.7% | 55 | 9 | 47 | 5 |
| **0.25 (Optimal Balanced)** | **89.7%** | **92.9%** | **86.7%** | **89.7%** | **52** | **4** | **52** | **8** |
| 0.30 | 89.7% | **100.0%** | 80.0% | 88.9% | 48 | 0 | 56 | 12 |
| **0.35 (Escalation Horizon)** | 87.1% | **100.0%** | 75.0% | 85.7% | 45 | **0** | **56** | 15 |
| 0.50 | 74.1% | **100.0%** | 50.0% | 66.7% | 30 | 0 | 56 | 30 |

*Empirical Finding*: At $\theta \ge 0.30$, precision reaches **100.0% with exactly zero false alarms** across all clean inputs. This proves why our escalation threshold $\theta_{\text{esc}} = 0.35$ eliminates false blocks on legitimate transactions.

### 3. Agentic Workflow Security Evaluation (1,060 Trajectory Runs)

Tested across 4 simulated Indian DPI environments with deterministic in-memory state machines:

| Metric | Vulnerable ReAct Agent | Prompt-Guarded Agent | Delta ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Clean Task Utility** | **100.0%** (30 / 30) | **100.0%** (30 / 30) | 0.0 pp |
| **Task Utility Under Attack** | 1.6% | **44.0%** | **+42.4 pp** |
| **Attack Success Rate (ASR)** | **61.6%** (308 / 500) | **2.4%** (12 / 500) | **$-$59.2 pp** |
| **Operational False-Block Rate** | **0.0%** (0 / 30) | **0.0%** (0 / 30) | **0.0 pp** |

---

## Quickstart & Installation

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/PrabhuVineeth/agentguard-in.git
cd agentguard-in

# Install dependencies in editable mode
pip install -r requirements.txt
pip install -e .
```

### 2. Verify Installation (63 Tests on CPU, <90s)

```bash
pytest -v tests/
```

### 3. Reproduce Empirical Benchmarks

```bash
# Evaluate Real-World Kaggle / Deepset Benchmark
python scripts/train_and_eval_real_dataset.py

# Run Phase 2 Scaled Agent Benchmark (1,060 Trajectories)
python scripts/run_scaled_benchmark.py --max_runs 500

# Run Phase 4 Graph Trajectory GNN Ablations
python scripts/train_and_eval_graph.py --epochs 20

# Run Phase 5 Layered Defense Combiner Evaluation
python scripts/run_end_to_end_eval.py
```

---

## Repository Structure

```text
agentguard_in/
├── .github/workflows/ci.yml # Automated GitHub Actions CI pipeline
├── configs/                 # YAML configuration (tasks, attacks, budgets)
├── data/
│   ├── attacks_benchmark.json
│   ├── tasks_benchmark.json
│   ├── cache/               # Deterministic LLM response cache
│   ├── models/              # Pretrained model checkpoints (text & GNN)
│   └── real_benchmark/      # Real-world Kaggle/Deepset CSV datasets
├── docs/                    # Architectural decisions, novelty notes, checklists
│   ├── architecture.md
│   ├── decisions.md
│   ├── novelty.md
│   ├── project_summary.md
│   └── checkpoints/         # Development phase sign-off records
├── paper/                   # Complete IEEE Conference Manuscript
│   ├── main.tex             # LaTeX source code (strict 6-page format)
│   ├── references.bib       # 20 literature benchmark citations
│   └── figures/             # Vector PDF & high-res PNG methodology diagrams
├── scripts/                 # Reproducibility evaluation and training CLI scripts
├── src/agentguard/          # Core Python package
│   ├── agents/              # Multi-turn ReAct loops & LLM adapters (Groq, OpenAI)
│   ├── attacks/             # 5 attack family generators & taint injection
│   ├── defense/             # Component D Layered Combiner (ALLOW/ESCALATE/BLOCK)
│   ├── graph/               # Component C GraphSAGE GNN & TrajectoryGraph
│   ├── guardrail/           # Component B Multilingual subword & Groq adapters
│   ├── logging/             # JSONL telemetry schema & provenance logger
│   ├── tasks/               # Deterministic DPI state machines (UPI, IRCTC, etc.)
│   └── tools/               # Mock privileged and observation tools
├── tests/                   # 63 pytest unit & integration tests
├── .env.example             # Template for API keys
├── .gitignore               # Strict exclusion of secrets and build files
├── CHANGELOG.md             # Version release history
├── CITATION.cff             # Academic citation metadata
├── CONTRIBUTING.md          # Open-source contribution guidelines
├── LICENSE                  # Apache 2.0 open-source license
├── LIMITATIONS.md           # Publication-standard limitations & threats to validity
├── pyproject.toml           # Modern PEP 517/621 packaging metadata
├── README.md                # Project documentation
├── requirements.txt         # Pinned production dependencies
├── RESULTS.md               # Detailed empirical results log
└── SECURITY.md              # Vulnerability disclosure policy
```

---

## Citation

If you use AgentGuard-IN in your research, please cite our IEEE conference paper:

```bibtex
@inproceedings{agentguardin2026,
  title     = {AgentGuard-IN: A Layered Defense Framework Against Indirect Prompt Injection on Tool-Using LLM Agents in Indian Digital Public Infrastructure},
  author    = {AgentGuard-IN Research Team},
  booktitle = {Proceedings of the IEEE International Conference on Artificial Intelligence and Cybersecurity},
  year      = {2026},
  pages     = {1--6},
  url       = {https://github.com/PrabhuVineeth/agentguard-in}
}
```

---

## Safety & Ethics Statement

Every tool in AgentGuard-IN operates strictly on **simulated, in-memory mock states**. No live network requests are dispatched to production banking portals, Indian Railways servers, government portals, or real email inboxes. All mock VPAs, PNRs, Aadhaar references, and bank ledgers are synthetic. The adversarial payloads and benchmark datasets are distributed under responsible vulnerability research practices to advance the defensive security of autonomous agents.
