"""JSONL Logger for AgentGuard-IN run trajectories."""

import json
from pathlib import Path
from typing import Iterator, List, Optional
from agentguard.logging.schema import TrajectoryRun


class TrajectoryLogger:
    """Manages appending and reading execution trajectories as JSONL."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_run(self, run: TrajectoryRun):
        """Append a completed trajectory run to the JSONL log file."""
        line = json.dumps(run.model_dump(), ensure_ascii=False)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read_runs(self) -> List[TrajectoryRun]:
        """Read all runs from log file."""
        if not self.log_path.exists():
            return []
        runs = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        runs.append(TrajectoryRun.model_validate_json(line))
                    except Exception as e:
                        pass
        return runs
