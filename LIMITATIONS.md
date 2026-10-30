# Limitations of AgentGuard-IN

This document is a publication-standard honest accounting of the **known limitations**, threats to validity, and open research questions for the AgentGuard-IN benchmark and defense framework.

---

## 1. Simulation Fidelity

**AgentGuard-IN evaluates against a deterministic mock tool environment**, not live banking, railway, or government portals. Real deployment surfaces the following gaps not captured by the benchmark:

- **Rate limiting and session tokens** — real APIs impose latency, CAPTCHA challenges, and session expiration that can alter agent behavior mid-trajectory.
- **Tool response variability** — mock tools always return structured deterministic JSON; real APIs return noisy, semi-structured, or error-prone responses.
- **Network latency** — real graph trajectories will have longer inter-step gaps, which may expose timing-based attacks not present in our dataset.

> **Implication**: Empirical ASR and defense F1 numbers reported here represent an upper bound of attack success in mock conditions; real-world ASR may differ in either direction depending on deployment-specific constraints.

---

## 2. Attack Family Coverage

The benchmark covers **5 attack families**: `direct_override`, `fake_system_alert`, `multi_step`, `obfuscated`, and `multi_lingual_social_engineering`. However:

- **Adaptive attacks** are not modeled — an adversary who knows the guardrail architecture could craft inputs specifically designed to evade the TF-IDF + Logistic Regression pipeline.
- **Indirect prompt injection via rendered HTML / markdown** (e.g., image alt-text, hyperlink labels) is out of scope for the current text-level Component B.
- **Cross-domain injection** (e.g., an attack embedded in a UPI QR code image that is OCR-decoded by the agent) is not covered.
- The multilingual attack coverage includes **English, Hindi (Devanagari), and Kannada** only; other Indian-language scripts (Tamil, Bengali, Telugu, Marathi) are excluded from the current benchmark.

---

## 3. Component B (Text Guardrail) Limitations

- The deployed classifier is a **TF-IDF + Logistic Regression pipeline** rather than a transformer model, despite the architecture name `distilbert-base-multilingual-cased` documented for the production target. This was a deliberate reproducibility trade-off (avoids GPU and HuggingFace Hub dependencies for local reproducibility).
- **Threshold sensitivity**: the optimal threshold (0.20) was calibrated on the held-out validation split; it may not generalize to out-of-distribution attack phrasing.
- **False-positive risk on legitimate multilingual inputs**: the regex baseline flags Cyrillic-lookalike characters (score 0.80); this may trigger false positives on legitimate content that contains Unicode homoglyphs for typographical purposes.

---

## 4. Component C (Graph Detector) Limitations

- **Post-hoc detection**: the graph-based detector requires at least one completed agent turn before a graph can be constructed. It cannot prevent the first privileged action in a zero-turn injection scenario.
- **Exclusion of synthetic 100% metrics from paper**: In early synthetic mock splits, GraphSAGE achieved 100% F1 and 1.000 ROC-AUC due to extreme 30:1 class imbalance (360 attacked vs. 12 clean) and rigid template structures. Because these metrics are misleading and unrepresentative of real-world deployments, they have been deliberately excluded from the publication manuscript and replaced with the canonical real-world benchmark (`deepset/prompt-injections`) where the model achieves a realistic **89.7% F1 and 0.971 ROC-AUC**.
- **Graph size distribution**: test graphs have a median of 6 nodes; large production agents with 50+ tool calls per session may require deeper GNN architectures or hierarchical graph representations.

---

## 5. Component D (Layered Combiner) Limitations

- **Static fusion weights**: the alpha hyperparameter is fixed at inference time. An adaptive combiner that adjusts weights based on domain (e.g., higher graph weight for multi-step workflows, higher text weight for single-turn queries) may improve performance.
- **Escalation policy is human-dependent**: the ESCALATE outcome assumes a human operator is available to confirm actions in real time. In fully automated deployments, ESCALATE effectively degrades to ALLOW, eliminating the three-way safety net.
- **No calibration of combined scores**: the combined score is a linear combination of independently-calibrated sub-scores; their product space is not jointly calibrated. ROC analysis on the fused score should be interpreted accordingly.

---

## 6. Evaluation Methodology Limitations

- **Train/test leakage risk**: all splits are generated programmatically from the same 4 task generators and 5 attack templates. Though splits are disjoint by `run_id`, the attack phrasing shares vocabulary, which inflates cross-split generalization estimates.
- **Bootstrap CI width**: with 372 test graphs, bootstrap CIs are computed with 500 resamples. For subgroup breakdowns (e.g., per language, per attack family), sample sizes drop to 60–120, making per-group CIs wider and less reliable.
- **Single random seed**: all experiments use `seed=42`. Results have not been replicated across multiple random seeds.

---

## 7. Novelty Scope

AgentGuard-IN's primary novelty is the **Indian-language, Indian-domain benchmark construction** and the **graph-based trajectory detection methodology**. The individual components (regex heuristics, TF-IDF classifiers, GraphSAGE, GAT) are established methods. The contribution lies in:

- Their integration into a unified multi-component pipeline,
- The novel heterogeneous graph schema (user_request → model_step → tool_call → tool_result with `is_untrusted` / `is_privileged` node attributes), and
- The domain-specific Indian workflow attack templates.

---

## 8. Reproducibility Constraints

- The benchmark requires **Python ≥ 3.10**, `torch`, `torch-geometric`, `scikit-learn`, `networkx`, `pydantic v2`, and `transformers`. Installation was verified on Python 3.12.4 on Windows 11.
- No cloud GPUs or paid API calls are required. All experiments ran on CPU in under 10 minutes total wall-clock time.
- The dataset (1,060 runs) is fully synthetic and included in the repository under `data/`. All random seeds are fixed.

---

*This document was last updated: 2026-10-28.*

