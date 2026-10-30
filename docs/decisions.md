# Architectural & Research Decisions (DECISIONS.md)

This log records every non-trivial design choice, trade-off, and rationale across the project.

---

## 1. Safety & Deterministic Mocking (Phase 1)
- **Decision**: Mock all 5 tools (`send_payment`, `read_email`, `send_email`, `book_ticket`, `read_document`) purely in-memory using dataclasses with an explicit event-sourcing trace log.
- **Rationale**: Completely isolates research runs from live networks, preventing accidental data leaks, API abuse, or unsafe execution while providing 100% deterministic ground-truth verification of execution outcomes.

## 2. Programmatic Evaluation vs LLM Judge (Phase 1)
- **Decision**: Task completion (utility) and Attack Success Rate (ASR) are evaluated strictly through deterministic predicate functions over the final mock environment state (e.g. check if `recipient == expected_recipient`, `balance_change == expected_amount`, or whether attacker account was credited).
- **Rationale**: LLM judges are prone to hallucinations, prompt injections, and evaluation drift. Programmatic verification ensures zero ambiguity and reproducible research numbers.

## 3. Data Leakage Prevention & Splits (Phase 1 & 2)
- **Decision**: Partition datasets strictly across two axes:
  1. Task identity (no identical tasks across train and test).
  2. Attack families (e.g., `multi_step` and `obfuscated` held out in test split).
- **Rationale**: Real-world attackers do not use the exact injection templates the defender trained on. Out-of-distribution (OOD) attack family evaluation is required for credible security benchmarks.

## 4. Multi-Provider LLM Abstraction with Deterministic Mock Adapter (Phase 1)
- **Decision**: Provide a unified `LLMClient` interface with adapters for OpenAI, Gemini, Hugging Face, Ollama, and a rule-based `MockLLMAdapter`.
- **Rationale**: Enables unit testing, local execution, and reproducibility without requiring external credits or paid APIs, while remaining drop-in ready for production LLMs.
