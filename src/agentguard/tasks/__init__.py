"""Tasks module for AgentGuard-IN."""

from agentguard.tasks.generator import (
    generate_benchmark_tasks,
    generate_phase1_tasks,
    load_tasks_from_disk,
    save_tasks_to_disk,
)
from agentguard.tasks.schema import (
    BenchmarkTask,
    ExpectedBooking,
    ExpectedPayment,
    ExpectedSentEmail,
    TaskSuccessCriteria,
    UntrustedSlot,
)

__all__ = [
    "BenchmarkTask",
    "UntrustedSlot",
    "TaskSuccessCriteria",
    "ExpectedPayment",
    "ExpectedBooking",
    "ExpectedSentEmail",
    "generate_benchmark_tasks",
    "generate_phase1_tasks",
    "save_tasks_to_disk",
    "load_tasks_from_disk",
]
