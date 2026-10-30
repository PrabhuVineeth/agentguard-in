"""Trajectory and run schemas with strict versioning for AgentGuard-IN."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

StepType = Literal["user_request", "model_step", "tool_call", "tool_result"]


class TrajectoryStep(BaseModel):
    """Atomic step in an agent's execution trajectory."""
    step_index: int
    step_type: StepType
    role: Literal["user", "assistant", "tool", "system"]
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    is_untrusted: bool = False
    parent_step_indices: List[int] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TrajectoryRun(BaseModel):
    """Complete record of a single benchmark task execution."""
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    schema_version: str = "1.0.0"
    task_id: str
    domain: str
    language: str = "en"
    split: str = "train"
    is_attacked: bool = False
    attack_id: Optional[str] = None
    attack_family: Optional[str] = None
    model_provider: str = "mock"
    model_name: str = "mock-v1"
    steps: List[TrajectoryStep] = Field(default_factory=list)
    task_success: bool = False  # Benign utility criterion
    attack_success: bool = False  # Malicious goal criterion
    blocked_by_defense: bool = False
    defense_decision: Optional[str] = None  # allow, block, ask-user
    execution_details: Dict[str, Any] = Field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_sec: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
