"""Groq-hosted Prompt Guard 2 Adapter for Component B Text Guardrail."""

import os
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from agentguard.guardrail.base import BaseTextGuardrail


class GroqPromptGuardrail(BaseTextGuardrail):
    """Component B Guardrail powered by Meta's Prompt Guard 2 (86M) via Groq's LPU.
    
    Model: meta-llama/llama-prompt-guard-2-86m
    Returns: Probability of prompt injection in [0.0, 1.0].
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "meta-llama/llama-prompt-guard-2-86m",
        timeout: float = 15.0,
    ):
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = model_name
        self.timeout = timeout
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def score(self, text: str) -> float:
        """Call Groq Prompt Guard 2 endpoint and return injection risk score."""
        if not text or not text.strip():
            return 0.0

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Provide api_key or set GROQ_API_KEY in .env file."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": text}],
            "temperature": 0.0,
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # The model outputs raw float string like "0.9996032118797302"
            raw_score = float(content.strip())
            return float(max(0.0, min(1.0, raw_score)))
        except Exception as e:
            # Fallback if network or quota issue
            return 0.5

