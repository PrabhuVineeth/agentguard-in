"""Unit tests for agent loop execution and trajectory logging."""

import pytest
from agentguard.agents.agent_loop import AgentRunner
from agentguard.agents.llm_client import MockLLMAdapter
from agentguard.attacks.injector import AttackInjector
from agentguard.tasks.generator import generate_phase1_tasks


def test_agent_runner_clean_task():
    tasks = generate_phase1_tasks()
    task = next(t for t in tasks if t.id == "TASK_UPI_001")

    client = MockLLMAdapter(mode="vulnerable")
    runner = AgentRunner(llm_client=client, max_steps=4)
    run = runner.run_task(task)

    assert run.task_id == "TASK_UPI_001"
    assert run.task_success is True
    assert run.attack_success is False
    assert len(run.steps) >= 3
    # Check steps types
    assert run.steps[0].step_type == "user_request"
    assert any(s.step_type == "tool_call" and s.tool_name == "read_email" for s in run.steps)
    assert any(s.step_type == "tool_call" and s.tool_name == "send_payment" for s in run.steps)


def test_agent_runner_attacked_task():
    tasks = generate_phase1_tasks()
    task = next(t for t in tasks if t.id == "TASK_UPI_001")

    injector = AttackInjector()
    template = injector.templates_by_family["direct_override"][0]
    attacked_task = injector.inject(task, template)

    # In vulnerable mode, mock LLM gets hijacked by the injection in the email body
    client = MockLLMAdapter(mode="vulnerable")
    runner = AgentRunner(llm_client=client, max_steps=5)
    run = runner.run_task(attacked_task)

    assert run.is_attacked is True
    assert run.attack_family == "direct_override"
    assert run.attack_success is True  # Successfully demonstrated vulnerability
