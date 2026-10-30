"""Unit tests for Phase 2 dataset scaling, splits, and multilingual coverage."""

import pytest
from agentguard.attacks.injector import AttackInjector
from agentguard.attacks.templates import get_default_attack_templates
from agentguard.tasks.generator import generate_benchmark_tasks


def test_scaled_tasks_count():
    tasks = generate_benchmark_tasks()
    assert len(tasks) >= 150
    assert len(tasks) == 160


def test_domain_distribution():
    tasks = generate_benchmark_tasks()
    domains = {}
    for t in tasks:
        domains[t.domain] = domains.get(t.domain, 0) + 1

    for d in ["upi_payment", "irctc_ticket", "govt_portal", "email_assistant"]:
        assert domains[d] == 40


def test_multilingual_coverage_ratio():
    tasks = generate_benchmark_tasks()
    indic_tasks = [t for t in tasks if t.language in ("hi", "kn")]
    ratio = len(indic_tasks) / len(tasks)
    # Must be at least 30% per Phase 2 instructions
    assert ratio >= 0.30
    assert ratio == 0.40  # Exactly 40% (64 / 160)


def test_split_and_leakage_controls():
    tasks = generate_benchmark_tasks()

    # Verify Kannada tasks are strictly held-out in test split
    kn_tasks = [t for t in tasks if t.language == "kn"]
    assert len(kn_tasks) > 0
    assert all(t.split == "test" for t in kn_tasks), "All Kannada tasks must be in held-out test split"

    # Verify human review metadata fields
    for t in tasks:
        assert hasattr(t, "human_reviewed")
        assert hasattr(t, "translation_source")
        assert t.translation_source in ("native_curated", "machine_translated", "synthetic")


def test_attack_families_in_test_split():
    templates = get_default_attack_templates()
    injector = AttackInjector(templates=templates)
    tasks = generate_benchmark_tasks()

    # Pick a test task and verify multi_step and obfuscated can be injected
    test_task = next(t for t in tasks if t.split == "test" and t.untrusted_slots)

    ms_template = next(t for t in templates if t.family == "multi_step")
    obf_template = next(t for t in templates if t.family == "obfuscated")

    mutated_ms = injector.inject(test_task, ms_template)
    assert mutated_ms.metadata["attack_family"] == "multi_step"

    mutated_obf = injector.inject(test_task, obf_template)
    assert mutated_obf.metadata["attack_family"] == "obfuscated"
