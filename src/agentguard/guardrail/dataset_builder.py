"""Dataset builder for Component B text guardrail training and evaluation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple
from agentguard.tasks.generator import load_tasks_from_disk
from agentguard.tasks.schema import BenchmarkTask


@dataclass
class TextSnippet:
    text: str
    label: int  # 0 = clean/benign, 1 = injected/malicious
    language: str
    split: Literal["train", "val", "test"]
    task_id: str
    attack_family: Optional[str] = None


def extract_guardrail_dataset(data_dir: Path) -> List[TextSnippet]:
    """Extract all untrusted content snippets labeled clean (0) or injected (1)."""
    clean_file = data_dir / "tasks_benchmark.json"
    attacks_file = data_dir / "attacks_benchmark.json"

    clean_tasks = load_tasks_from_disk(clean_file)
    attacked_tasks = load_tasks_from_disk(attacks_file)

    snippets: List[TextSnippet] = []

    # 1. Clean snippets (Label 0)
    for t in clean_tasks:
        for slot in t.untrusted_slots:
            content = slot.original_content
            if content and len(content.strip()) > 5:
                snippets.append(
                    TextSnippet(
                        text=content.strip(),
                        label=0,
                        language=t.language,
                        split=t.split,
                        task_id=t.id,
                        attack_family=None,
                    )
                )

    # 2. Injected snippets (Label 1)
    for at in attacked_tasks:
        for slot in at.untrusted_slots:
            content = slot.injected_content
            if content and len(content.strip()) > 5:
                snippets.append(
                    TextSnippet(
                        text=content.strip(),
                        label=1,
                        language=at.language,
                        split=at.split,
                        task_id=at.id,
                        attack_family=at.metadata.get("attack_family"),
                    )
                )

    return snippets
