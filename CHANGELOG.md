# Changelog (CHANGELOG.md)

All notable changes to the AgentGuard-IN project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-10-18 (Phase 1 Initial Foundation)
### Added
- Project repository scaffold, configuration files (`budget.yaml`, `tasks.yaml`, `attacks.yaml`, `models.yaml`), and documentation.
- Mock tools (`send_payment`, `read_email`, `send_email`, `book_ticket`, `read_document`) with deterministic in-memory state and audit logs.
- Pydantic task schema supporting 4 Indian-context domains (UPI, IRCTC, Govt, Email) and programmatic success predicates.
- 40 generated benign tasks across 4 domains.
- Attack injector library with 5 attack families (`direct_override`, `hidden_text`, `fake_system_message`, `multi_step`, `obfuscated`).
- Unified `LLMClient` with adapters for OpenAI, Gemini, Hugging Face, Ollama, and Mock LLM.
- Agent function-calling execution loop with trajectory tracking and untrusted-slot attribution.
- JSONL trajectory logging with schema versioning.
- Evaluation metrics suite computing ASR, Utility, and False-Block Rate.
- Comprehensive test suite for tools, tasks, attacks, and metrics.

## [0.6.0] - 2026-10-30 (Phase 6: Real-World Benchmark, Groq LPU & IEEE Manuscript)
### Added
- **Real-World Benchmark Integration** (`deepset/prompt-injections`):
  - Ingested 662 real-world prompt injection and jailbreak samples into `data/real_benchmark/`.
  - Added `scripts/train_and_eval_real_dataset.py` running comparative evaluations.
  - Demonstrated that composite training resolves synthetic shortcut collapse, boosting wild attack F1 from 45.8% to **89.7%** (0.971 ROC-AUC).
- **Groq LPU Acceleration**:
  - Implemented `GroqPromptGuardrail` calling `meta-llama/llama-prompt-guard-2-86m`.
  - Added unit test suite in `tests/test_real_and_groq.py`.
- **IEEE Conference Paper Package** (`paper/`):
  - Full 6-page IEEEtran manuscript (`paper/main.tex`).
  - BibTeX reference catalog with 20 literature benchmark citations (`paper/references.bib`).
  - High-resolution vector PDF (`figures/methodology.pdf`) and 300 DPI raster (`figures/methodology.png`) methodology architecture diagrams.
  - Script generator `scripts/generate_methodology_figure.py`.
- **Open-Source Production Hardening**:
  - Added Apache-2.0 `LICENSE`, `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.env.example`, and `.github/workflows/ci.yml`.
  - Reorganized internal development milestone checkpoints to `docs/checkpoints/`.
  - Pinned production requirements and modernized `pyproject.toml` metadata.
  - Total pytest suite: **63 tests / 63 passed (100%)**.
### Added
- **Component D: `LayeredDefenseCombiner`** (`src/agentguard/defense/`):
  - `combiner.py`: Weighted score fusion (alpha · text_score + (1-alpha) · graph_score) with configurable ALLOW / ESCALATE / BLOCK thresholds.
  - `__init__.py`: Clean public API.
- **`scripts/run_end_to_end_eval.py`**: End-to-end pipeline evaluation script loading saved B and C models, scoring test set, fusing across 5 alpha configurations, computing bootstrap CIs, and generating IEEE LaTeX table.
- **`tests/test_defense.py`**: 26 new pytest tests for Component D (decision outcomes, alpha weighting, score clamping, text/graph-only modes, batch inference, parameter validation, threshold sweep).
- **`LIMITATIONS.md`**: IEEE-grade limitations document covering 8 limitation categories.
- **`PROJECT_SUMMARY.md`**: Complete project overview with abstract, architecture diagram, empirical results, reproducibility guide, and BibTeX citation.
- **`CHECKPOINT_PHASE_5.md`**: Phase 5 completion checkpoint.

### Changed
- `RESULTS.md`: Phase 5 Component D evaluation results appended.
- Total pytest suite: **60 tests / 60 passed (100%)**.
