"""Keyword and regex-based prompt injection detector baseline."""

import re
from typing import List, Pattern, Tuple
from agentguard.guardrail.base import BaseTextGuardrail


class RegexGuardrail(BaseTextGuardrail):
    """Fast regex and keyword heuristic guardrail baseline."""

    PATTERNS: List[Tuple[str, float]] = [
        # Direct override signals
        (r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:prior|previous)\s+instructions\b", 0.95),
        (r"\bnew\s+operating\s+instructions\b", 0.90),
        (r"\bsystem\s+prompt\s+reset\b", 0.95),
        (r"\bmandatory\s+(?:high-priority\s+)?directive\b", 0.85),
        # Simulated system message spoofing
        (r"\[SYSTEM\s+(?:MESSAGE|NOTIFICATION|ALERT)[^\]]*\]", 0.90),
        (r"===+\s*NEW\s+OPERATING\s+INSTRUCTIONS\s*===+", 0.90),
        # Dangerous tool invocation commands inside untrusted data
        (r"\bsend_payment\s*\(", 0.95),
        (r"s\s*e\s*n\s*d\s*_\s*p\s*a\s*y\s*m\s*e\s*n\s*t", 0.95),
        # Hidden comments or footnotes with directives
        (r"<!--\s*automated\s+processing\s+metadata", 0.90),
        (r"<!--\s*system\s+instruction:", 0.95),
        # Zero-width spaces or hidden unicode
        (r"[\u200b\u200c\u200d\ufeff]", 0.85),
        # Cyrillic lookalikes in predominantly Latin text
        (r"[а-яА-Я]", 0.80),
        # Multi-step manipulation markers
        (r"Workflow\s+Protocol\s+Section\s+\d", 0.80),
        (r"double-entry\s+escrow\s+transfer", 0.85),
        (r"instant\s+cashback\s+of\s+INR", 0.75),
    ]

    def __init__(self):
        self._compiled: List[Tuple[Pattern, float]] = [
            (re.compile(p, re.IGNORECASE), weight) for p, weight in self.PATTERNS
        ]

    def score(self, text: str) -> float:
        """Return maximum matching heuristic risk score."""
        if not text:
            return 0.0

        max_risk = 0.0
        for pat, weight in self._compiled:
            if pat.search(text):
                if weight > max_risk:
                    max_risk = weight

        return max_risk
