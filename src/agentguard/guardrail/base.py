"""Base classes and interfaces for Component B text guardrails."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GuardrailPrediction(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Predicted probability of prompt injection")
    is_injected: bool = Field(description="Binary classification based on operating threshold")
    threshold: float = 0.5
    latency_ms: float = 0.0
    model_name: str = "guardrail_base"
    metadata: Dict[str, float] = Field(default_factory=dict)


class BaseTextGuardrail(ABC):
    """Abstract base class for prompt-injection text guardrails."""

    @abstractmethod
    def score(self, text: str) -> float:
        """Return raw injection risk score in [0.0, 1.0]."""
        pass

    def predict(self, text: str, threshold: float = 0.5) -> GuardrailPrediction:
        """Classify text against an operational decision threshold."""
        import time
        t0 = time.time()
        raw_score = float(max(0.0, min(1.0, self.score(text))))
        latency = (time.time() - t0) * 1000.0
        return GuardrailPrediction(
            score=raw_score,
            is_injected=raw_score >= threshold,
            threshold=threshold,
            latency_ms=latency,
            model_name=self.__class__.__name__,
        )
