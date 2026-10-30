"""Mock tools package for AgentGuard-IN."""

from agentguard.tools.base import ToolCallRecord, ToolDefinition, ToolParameter
from agentguard.tools.environment import (
    MockAccount,
    MockDocument,
    MockEmail,
    MockEnvironmentState,
    MockTrain,
    MockTrainBooking,
)
from agentguard.tools.mock_tools import (
    MockToolRegistry,
    book_ticket,
    read_document,
    read_email,
    send_email,
    send_payment,
)

__all__ = [
    "ToolDefinition",
    "ToolParameter",
    "ToolCallRecord",
    "MockAccount",
    "MockEmail",
    "MockTrain",
    "MockTrainBooking",
    "MockDocument",
    "MockEnvironmentState",
    "MockToolRegistry",
    "send_payment",
    "read_email",
    "send_email",
    "book_ticket",
    "read_document",
]
