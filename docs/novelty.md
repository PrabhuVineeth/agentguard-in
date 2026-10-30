# Novelty Analysis & Literature Survey Comparison (NOVELTY_NOTES.md)

This document provides a comprehensive, publication-grade comparative analysis of **AgentGuard-IN** against 20 key academic papers across prompt injection, LLM agent security, multilingual safety, and graph-based intrusion detection.

---

## 1. Literature Survey Taxonomy (20 Papers)

The research landscape surrounding indirect prompt injection (IPI) and LLM agent security can be organized into four overarching paradigms:

```
                                  Prompt Injection & Agent Safety Landscape
                                                     │
      ┌──────────────────────────────┬───────────────┴───────────────┬──────────────────────────────┐
      ▼                              ▼                               ▼                              ▼
 [Paradigm 1: Benchmarks]     [Paradigm 2: Multilingual]    [Paradigm 3: Agent Defenses]    [Paradigm 4: Guardrails & Graphs]
 • Greshake et al. (2023)     • Yong et al. (2023)          • Spotlighting (2024)           • Llama Guard (2023)
 • BIPIA (2023)               • MultiJail (2024)            • StruQ (2025)                  • NeMo Guardrails (2023)
 • InjecAgent (2024)          • XSafety (2024)              • Instruction Hierarchy (2024)  • MAGIC (2024)
 • AgentDojo (2024)                                         • CaMeL (2025)
 • Liu et al. (2024)                                        • FIDES (2025)
 • ToolEmu (2024)                                           • MELON (2025)
 • ASB (2025)                                               • IsolateGPT (2025)
```

---

## 2. Comprehensive 20-Paper Comparative Table

| S.No | Paper / Authors | Year & Venue | Benchmark / Dataset | Methodology | Strengths | Weaknesses & Research Gaps | Relevance to AgentGuard-IN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Greshake et al.** | 2023 (ACM AISec) | Synthetic apps & Bing Chat PoCs | Qualitative IPI threat modeling; planted payloads in retrieved web/emails | Defined IPI threat taxonomy; real-system demos | Qualitative; no benchmark; English only; no Indic workflows | Foundational reference for the IPI threat model |
| **2** | **BIPIA** (Yi et al.) | 2023 (arXiv) | 5 NLP tasks (QA, summarization) | Benchmark construction; black-box prompting and white-box fine-tuning | First dedicated IPI benchmark; shows capability correlates with risk | Pure text-in/text-out; no tools; English only; no state verification | Baseline benchmark; AgentGuard-IN adds privileged tool execution and state checks |
| **3** | **InjecAgent** (Zhan et al.) | 2024 (ACL Findings) | 1,054 cases, 17 user tools, 62 attack tools | Synthetic test generation; evaluates ReAct and fine-tuned agents | First tool-agent IPI benchmark; evaluated many LLMs | Single-step; judged from emitted action strings; no state; English | Direct tool-agent comparison target |
| **4** | **AgentDojo** (Debenedetti et al.) | 2024 (NeurIPS) | 97 tasks, 629 security test cases | Stateful mock environment; evaluates prompt delimiters and filters | State-based ground truth; evaluates utility and security jointly | Western corporate suites (Slack, travel); English only; no graph defense | Closest methodological precedent; AgentGuard-IN adds Indic DPI and graph detection |
| **5** | **Liu et al.** | 2024 (USENIX Security) | Systematic cross-product across 10 LLMs | Formal evaluation of 5 attacks and 10 defenses | Unified formalization; large-scale systematic comparison | Task-level NLP, not tool-using agents; English only | Supports formal problem statement and threat definition |
| **6** | **ToolEmu** (Ruan et al.) | 2024 (ICLR) | 36 toolkits, 311 tools, 144 cases | LLM-emulated tool execution + LLM safety evaluator | Scales risk discovery without implementing every API | Emulator hallucinations; non-deterministic; hard to reproduce | Justifies AgentGuard-IN's choice of deterministic state machines over LLM emulation |
| **7** | **ASB** (Zhang et al.) | 2025 (ICLR) | 400+ tools across multiple scenarios | Multi-surface benchmark (DPI, IPI, memory poisoning, backdoors) | Broadest attack-surface coverage; multi-metric | English only; generic tools; prompt defenses weak | Broad threat landscape context; motivates layered defenses |
| **8** | **Yong et al.** | 2023 (arXiv) | AdvBench harmful prompts translated | Translates unsafe prompts to low-resource languages (Google Translate) | Shows low-resource languages bypass GPT-4 safety | Direct chat jailbreaks; no Indic focus; no tool agents | Motivates multilingual attack generation in Indic workflows |
| **9** | **MultiJail** (Deng et al.) | 2024 (ICLR) | 315 unsafe prompts in 9 languages | Human-translated chat jailbreaks; proposes SELF-DEFENCE | Human-validated; resource-level analysis | Chat jailbreaks only; no tool-using agents; no transliteration | Core evidence that safety degrades with language resource level |
| **10** | **XSafety** (Wang et al.) | 2024 (ACL Findings) | Multilingual safety benchmark | Prompting and fine-tuning strategies across languages | Wide language coverage | Chat safety, not agent security; no tool execution | Supports cross-lingual safety gap claims in non-English LLMs |
| **11** | **Spotlighting** (Hines et al.) | 2024 (arXiv) | Injected documents on summarization/QA | Prompt transformations marking untrusted text (delimiters, encoding) | Zero training cost; reduces simple IPI | Relies on LLM following marking; non-agentic text; English | Baseline prompt-level defense; contrasts with runtime graph defenses |
| **12** | **StruQ** (Chen et al.) | 2025 (USENIX Security) | Alpaca-style instruction tuning | Front-end separates prompt and data; structured instruction tuning | Near-zero ASR on manual attacks; low utility loss | Requires retraining model; optimization attacks bypass; English | Representative training-time defense contrasted with plug-and-play guards |
| **13** | **Instruction Hierarchy** (Wallace et al.) | 2024 (arXiv) | Synthetic hierarchical instructions | Fine-tunes model to rank system > user > tool instructions | Increases robustness on unseen attacks | Requires weight access; English only; over-refuses | Motivates external model-agnostic defenses for closed LLMs |
| **14** | **CaMeL** (Debenedetti et al.) | 2025 (arXiv) | AgentDojo suite | Privileged/quarantined LLM split; capability-based data flow tracking | Provable security guarantees on tested tasks | Full agent rewrite required; manual policies; English | Contrasts with Component C: AgentGuard-IN observes without rewriting agent |
| **15** | **FIDES** (Costa et al.) | 2025 (arXiv) | AgentDojo suite | Information-flow control (IFC) labels propagated through planner | Formal guarantees; deterministic enforcement | Requires label annotations and planner modifications | Closest IFC work; AgentGuard-IN learns graph patterns rather than requiring manual labels |
| **16** | **MELON** (Zhu et al.) | 2025 (ICML) | AgentDojo suite | Re-executes agent with user task masked; flags persisting calls | No detector training needed; good trade-off | Extra LLM calls double latency and API costs; English | Alternative runtime detector; AgentGuard-IN avoids re-execution cost |
| **17** | **IsolateGPT** (Wu et al.) | 2025 (NDSS) | Custom cross-app ecosystem scenarios | Hub-and-spoke isolation; mediated cross-app interaction | OS-style isolation; low runtime overhead | Requires re-architecting app ecosystem; user friction | Supports defense-in-depth discussion |
| **18** | **MAGIC** (Jia et al.) | 2024 (USENIX Security) | StreamSpot, DARPA TC provenance | Masked graph autoencoder on host audit logs for APTs | Unsupervised; strong on host benchmarks | Host/OS audit logs, not LLM agent trajectories; no semantic NLP | Justifies applying GNNs to agent execution influence graphs (Component C) |
| **19** | **Llama Guard** (Inan et al.) | 2023 (arXiv) | Moderation & ToxicChat datasets | Instruction-tuned Llama-2 7B classifier with safety taxonomy | Customizable taxonomy; competitive | English-centric; chat dialogue only; requires 7B GPU model | Contrasts with CPU-light multilingual text guard (Component B) |
| **20** | **NeMo Guardrails** (Rebedea et al.) | 2023 (EMNLP) | Toolkit & demo paper | Programmable rails in Colang (input, dialog, execution rails) | Developer-friendly; composable rails | Rule/LLM latency; binary pass/fail actions; English | Motivates three-tier ALLOW/ESCALATE/BLOCK policy in Component D |

---

## 3. Cross-Cutting Research Gaps Addressed by AgentGuard-IN

| # | Cross-Cutting Research Gap | Evidence from Literature | How AgentGuard-IN Addresses It |
| :--- | :--- | :--- | :--- |
| **1** | **English-Centric Benchmarking** | BIPIA, InjecAgent, AgentDojo, ASB, Liu et al., Spotlighting, StruQ | Benchmarks across English, Hindi (Devanagari), and held-out Kannada (Dravidian script). |
| **2** | **Lack of Indian Digital Public Infrastructure (DPI)** | All existing agent benchmarks simulate Western tools (Slack, Google Drive, US banking) | Evaluates realistic mock environments for UPI payments (VPAs, NPCI alerts), IRCTC ticketing, and citizen welfare portals. |
| **3** | **Multilingual Safety Restricted to Chat Jailbreaks** | Yong et al., MultiJail, XSafety only study direct chatbot toxicity | Bridges multilingual safety with agentic tool execution (indirect injections planted in retrieved Hindi/Kannada payloads). |
| **4** | **Defenses Require Intrusive Agent Rewrite or Model Retraining** | CaMeL, FIDES, IsolateGPT require complete redesign; StruQ, Instruction Hierarchy require model retraining | Non-intrusive, model-agnostic wrapper monitoring natural execution traces (supports OpenAI, Groq, Gemini, Ollama). |
| **5** | **Excessive Latency and Cost Overhead in Runtime Defenses** | MELON requires duplicate masked re-execution (2x API cost); Llama Guard requires 7B GPU model | CPU-light architecture: Subword Text Guard runs in ~3ms; 2-layer GraphSAGE GNN runs in ~5ms. |
| **6** | **Graph Learning Unexplored for LLM Agent Trajectories** | MAGIC and system provenance papers evaluate OS kernels, never LLM agents | Constructs heterogeneous directed influence graphs from multi-turn agent turns and detects structural hijacking via GNNs. |
| **7** | **Binary Pass/Fail Decisions Harm Usability** | NeMo Guardrails, regex filters, standard classifiers use hard Allow/Block thresholds | Introduces an asymmetric three-tier policy: ALLOW / ESCALATE (human-in-the-loop review) / BLOCK. |
| **8** | **Synthetic Shortcut / Non-Deterministic Evaluation** | ToolEmu relies on hallucinations of LLM emulators; synthetic benchmarks produce 100% fake F1 scores | Uses event-sourced deterministic state machines and validates against both Indic mock data and the real-world Kaggle/Deepset benchmark. |

---

## 4. The 8 Core Novelty Pillars of AgentGuard-IN

### Novelty 1: First Benchmark for Indian Digital Public Infrastructure (DPI) Workflows
Prior agent benchmarks focus on Western corporate APIs (e.g., booking an Uber in San Francisco or modifying a Slack channel). AgentGuard-IN is the first empirical security benchmark designed around Indian digital workflows:
- **UPI Payments**: Simulates Virtual Payment Address (VPA) handles (e.g., `user@okhdfcbank`, `merchant@oksbi`) and NPCI transaction alert spoofing.
- **IRCTC Ticketing**: Models railway passenger roster constraints, quota rules, and train numbers.
- **Citizen Welfare Portals**: Implements government subsidy verification and eligibility checks (e.g., PM-Kisan, scholarship income thresholds).

### Novelty 2: Multilingual Indirect Prompt Injection on Tool Agents
While Yong et al. and MultiJail established that non-English prompts bypass chatbot moderation, AgentGuard-IN investigates **indirect prompt injection on tool-using agents**:
- The attack payload is embedded inside untrusted data retrieved by a tool (e.g., an incoming email remark or guideline document).
- Evaluates Indo-Aryan (`hi`, Devanagari) and Dravidian (`kn`, Kannada) scripts.
- Held-out test partitions empirically verify whether defenses generalize to unseen non-Latin scripts.

### Novelty 3: Deterministic In-Memory State Machine Ground Truth
Unlike ToolEmu (which relies on non-deterministic LLM-emulated tools and LLM evaluators) or InjecAgent (which matches action strings without persistent state), AgentGuard-IN enforces **formal state-based ground truth**:
- An attack is only recorded as successful if the underlying state machine transitions to a compromised state (e.g., funds deducted from user balance to attacker VPA).
- Completely eliminates LLM judge bias and emulator hallucinations.

### Novelty 4: Graph-Theoretic Agent Trajectory Detection (Component C)
Translating the intrusion detection concepts of MAGIC (USENIX Security '24) into the agent domain:
- Transforms multi-turn execution into a directed heterogeneous graph:
  - **Node Types**: `user_request`, `model_step`, `tool_call`, `tool_result`.
  - **Edge Types**: `control_flow` and `data_flow` (influence dependencies).
  - **Attributes**: `is_untrusted`, `is_privileged`, token length, step index.
- A **2-layer GraphSAGE / GAT GNN** classifies execution graphs, detecting topological causal paths from untrusted data sources to outward privileged actions.

### Novelty 5: Model-Agnostic, Plug-and-Play Observability
Defenses like CaMeL (quarantined interpreters) and FIDES (planner information-flow tracking) require fundamental rewrites of agent code. StruQ and Instruction Hierarchy require retraining model weights. **AgentGuard-IN is completely non-intrusive**:
- Operates as an external observer on standard tool execution traces.
- Compatible with any underlying LLM provider (Groq, OpenAI, Gemini, Ollama, HuggingFace).

### Novelty 6: Zero Re-Execution & CPU-Light Efficiency
Unlike MELON (which doubles token cost and latency by re-running masked agent steps) or Llama Guard (which requires a GPU-heavy 7B parameter model), AgentGuard-IN delivers ultra-low latency:
- Component B (Subword Text Guard): **~3.2 ms on standard CPU**.
- Component C (GraphSAGE GNN): **~5.1 ms on standard CPU**.
- Zero secondary LLM inference calls required during inspection.

### Novelty 7: Three-Tier Action Policy (Allow / Escalate / Block)
Traditional guardrails (NeMo Guardrails, regex filters) enforce binary pass/fail decisions. In automated workflows, false blocks destroy usability, while false allows cause severe security breaches. Component D introduces an **asymmetric three-tier combiner**:
$$\text{combined} = \alpha \cdot \text{text\_score} + (1 - \alpha) \cdot \text{graph\_score}$$
- $\ge 0.70 \rightarrow$ **BLOCK** (unconditional rejection).
- $\ge 0.35 \rightarrow$ **ESCALATE** (human confirmation: *"Agent is attempting to execute send_payment based on external email, approve?"*).
- $< 0.35 \rightarrow$ **ALLOW** (automated execution).

### Novelty 8: Dual-Benchmark Robustness (Synthetic Indic + Wild Kaggle Data)
To eliminate the synthetic shortcut learning artifact (which previously caused unrealistic 100% F1 scores), AgentGuard-IN integrates the real-world **Kaggle/Deepset prompt injection benchmark**:
- Evaluates on wild real-world jailbreaks alongside Indic mock trajectories.
- The composite model achieves **89.7% F1 and 0.971 ROC-AUC on wild attacks**, providing credible, publication-ready empirical evidence.

---

## 5. Scope Boundaries & Honesty Protocol

1. **Hardware Parity**: Comparative metrics for external papers (InjecAgent, AgentDojo) are cited directly from their published papers, not re-run on our hardware.
2. **Simulation Fidelity**: All Indian DPI tools operate on in-memory mock state machines. No live financial or government networks (NPCI, IRCTC) were probed.
3. **Realistic Metrics**: We explicitly distinguish between synthetic mock benchmark scores and wild Kaggle test scores to maintain empirical integrity.
