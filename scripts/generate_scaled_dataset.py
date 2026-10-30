#!/usr/bin/env python3
"""Generate scaled benchmark dataset (160+ tasks, 1000+ attacks) with strict split partitions."""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentguard.attacks.injector import AttackInjector
from agentguard.attacks.templates import get_default_attack_templates
from agentguard.tasks.generator import generate_benchmark_tasks, save_tasks_to_disk
from agentguard.tasks.schema import BenchmarkTask


def build_scaled_dataset():
    tasks = generate_benchmark_tasks()
    templates = get_default_attack_templates()
    injector = AttackInjector(templates=templates)

    # 1. Save clean benign tasks
    data_dir = Path(__file__).resolve().parent.parent / "data"
    tasks_path = data_dir / "tasks_benchmark.json"
    save_tasks_to_disk(tasks, tasks_path)
    print(f"Saved {len(tasks)} benign tasks to {tasks_path}")

    # 2. Generate attacked tasks
    # Hard Rule 6: No Leakage.
    # Train/Val families: direct_override, hidden_text, fake_system_message
    # Held-out Test families: multi_step, obfuscated
    train_val_families = {"direct_override", "hidden_text", "fake_system_message"}
    test_families = {"multi_step", "obfuscated"}

    attacked_tasks: List[BenchmarkTask] = []
    task_idx = 0

    for task in tasks:
        if not task.untrusted_slots:
            continue

        # Determine which templates apply according to split
        if task.split in ("train", "val"):
            eligible_templates = [t for t in templates if t.family in train_val_families]
        else:  # test split
            # Include all families, especially the held-out ones
            eligible_templates = templates

        for template in eligible_templates:
            task_idx += 1
            mutated = injector.inject(task, template)
            mutated.id = f"{task.id}_ATK_{template.id}_{task_idx:04d}"
            # Preserve or assign split consistent with task
            mutated.split = task.split
            attacked_tasks.append(mutated)

    attacks_path = data_dir / "attacks_benchmark.json"
    save_tasks_to_disk(attacked_tasks, attacks_path)
    print(f"Saved {len(attacked_tasks)} attacked benchmark instances to {attacks_path}")

    # 3. Compute and print dataset statistics
    print("\n" + "=" * 70)
    print("DATASET STATISTICS REPORT (AgentGuard-IN)")
    print("=" * 70)

    # By domain
    print("Tasks by Domain:")
    domain_counts = {}
    for t in tasks:
        domain_counts[t.domain] = domain_counts.get(t.domain, 0) + 1
    for dom, cnt in sorted(domain_counts.items()):
        print(f"  - {dom:<20}: {cnt} tasks")

    # By language
    print("\nTasks by Language:")
    lang_counts = {}
    for t in tasks:
        lang_counts[t.language] = lang_counts.get(t.language, 0) + 1
    for lang, cnt in sorted(lang_counts.items()):
        pct = (cnt / len(tasks)) * 100
        print(f"  - {lang:<10}: {cnt} tasks ({pct:.1f}%)")

    # By split
    print("\nTasks by Split:")
    split_counts = {}
    for t in tasks:
        split_counts[t.split] = split_counts.get(t.split, 0) + 1
    for sp, cnt in sorted(split_counts.items()):
        print(f"  - {sp:<10}: {cnt} tasks")

    # Attacked instances by Family
    print("\nAttacked Instances by Attack Family:")
    family_counts = {}
    for a in attacked_tasks:
        fam = a.metadata.get("attack_family", "unknown")
        family_counts[fam] = family_counts.get(fam, 0) + 1
    for fam, cnt in sorted(family_counts.items()):
        print(f"  - {fam:<25}: {cnt} runs")

    # Attacked instances by Split & Family
    print("\nAttacked Instances by Split:")
    att_split_counts = {}
    for a in attacked_tasks:
        att_split_counts[a.split] = att_split_counts.get(a.split, 0) + 1
    for sp, cnt in sorted(att_split_counts.items()):
        print(f"  - {sp:<10}: {cnt} runs")

    print("=" * 70)
    return tasks, attacked_tasks


if __name__ == "__main__":
    build_scaled_dataset()
