# Contributing to AgentGuard-IN

Thank you for your interest in contributing to **AgentGuard-IN**! We welcome research contributions, bug fixes, new domain environments, and novel defense algorithms.

---

## 1. Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 2. Development Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- Standard C++ build tools (for PyTorch / torch-geometric if building from source)

### Local Environment Installation

```bash
# Clone repository
git clone https://github.com/PrabhuVineeth/agentguard-in.git
cd agentguard-in

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

---

## 3. Running the Test Suite

Before submitting any code changes, ensure all unit and integration tests pass:

```bash
# Run complete test suite
pytest -v tests/

# Run specific component tests
pytest tests/test_defense.py
pytest tests/test_graph.py
pytest tests/test_guardrail.py
```

All tests run locally on standard CPU without requiring cloud GPUs or paid external API keys.

---

## 4. Coding Standards

- **Formatting & Linting**: We follow standard PEP 8 conventions.
- **Type Annotations**: All public functions and class methods must include Python type hints (`typing`).
- **Docstrings**: Document modules, classes, and public functions with clear parameters and return descriptions.
- **Deterministic State Machines**: Any new tool or environment must operate on deterministic, in-memory state machines with reproducible state predicates.
- **No Hardcoded Credentials**: Never commit secrets or API keys. Always use environment variables via `.env`.

---

## 5. Adding New Benchmark Domains or Attacks

### Adding a New Workflow Domain
1. Define the deterministic state model in `src/agentguard/tasks/`.
2. Implement mock tools adhering to `BaseTool` in `src/agentguard/tools/`.
3. Add task templates in `configs/tasks.yaml`.
4. Include programmatic assertion predicates to verify true state changes.

### Adding an Attack Family
1. Register the attack schema in `src/agentguard/attacks/`.
2. Add injection patterns across English, Hindi, and Kannada.
3. Validate that attacks cleanly target untrusted tool observation slots without corrupting system prompts.

---

## 6. Pull Request Process

1. Fork the repository and create a feature branch (`git checkout -b feature/your-feature-name`).
2. Commit your changes with clear, semantic commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
3. Ensure the test suite passes 100% (`pytest tests/`).
4. Submit a Pull Request targeting the `main` branch with a comprehensive description of the changes and empirical verification.

