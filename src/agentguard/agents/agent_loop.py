"""Multi-turn tool-using agent execution loop for AgentGuard-IN."""

import time
from typing import Any, Callable, Dict, List, Optional
from agentguard.agents.llm_client import BaseLLMAdapter, LLMMessage, LLMToolCall
from agentguard.attacks.schema import AttackGoal
from agentguard.logging.schema import TrajectoryRun, TrajectoryStep
from agentguard.tasks.schema import BenchmarkTask
from agentguard.tools.environment import MockEnvironmentState
from agentguard.tools.mock_tools import MockToolRegistry


class AgentRunner:
    """Executes a benchmark task against an LLM client in the mock environment."""

    def __init__(
        self,
        llm_client: BaseLLMAdapter,
        max_steps: int = 6,
        provider_name: str = "mock",
        model_name: str = "mock-v1",
        defense_hook: Optional[Callable[[List[TrajectoryStep], MockEnvironmentState], Dict[str, Any]]] = None,
    ):
        self.llm_client = llm_client
        self.max_steps = max_steps
        self.provider_name = provider_name
        self.model_name = model_name
        self.defense_hook = defense_hook

    def run_task(self, task: BenchmarkTask, base_env: Optional[MockEnvironmentState] = None) -> TrajectoryRun:
        """Execute a task and produce a complete trajectory run."""
        start_time = time.time()
        env = task.prepare_environment(base_env)
        initial_state = env.clone()

        # Tools allowed for this task
        tools_schema = MockToolRegistry.get_openai_tools(task.tools_allowed)

        # Track trajectory steps
        steps: List[TrajectoryStep] = []
        messages: List[LLMMessage] = []

        total_prompt_tokens = 0
        total_completion_tokens = 0

        # Step 0: User request
        user_step_idx = 0
        user_step = TrajectoryStep(
            step_index=user_step_idx,
            step_type="user_request",
            role="user",
            content=task.user_instruction,
            is_untrusted=False,
            parent_step_indices=[],
        )
        steps.append(user_step)
        messages.append(LLMMessage(role="user", content=task.user_instruction))

        blocked_by_defense = False
        defense_decision = None
        turn = 0
        last_influencing_step_idx = user_step_idx

        while turn < self.max_steps:
            turn += 1

            # Check defense hook before model generation if configured
            if self.defense_hook is not None:
                defense_eval = self.defense_hook(steps, env)
                if defense_eval.get("decision") == "block":
                    blocked_by_defense = True
                    defense_decision = "block"
                    break

            # LLM Generation
            response = self.llm_client.generate(messages=messages, tools=tools_schema)
            total_prompt_tokens += response.prompt_tokens
            total_completion_tokens += response.completion_tokens

            # Record model step
            model_step_idx = len(steps)
            model_step = TrajectoryStep(
                step_index=model_step_idx,
                step_type="model_step",
                role="assistant",
                content=response.content,
                is_untrusted=False,
                parent_step_indices=[last_influencing_step_idx],
            )
            steps.append(model_step)

            # If no tool calls, task execution is finished
            if not response.tool_calls:
                messages.append(LLMMessage(role="assistant", content=response.content))
                break

            # Add assistant message with tool calls
            messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            # Execute tool calls
            tool_result_indices = []
            for tc in response.tool_calls:
                tc_step_idx = len(steps)
                tc_step = TrajectoryStep(
                    step_index=tc_step_idx,
                    step_type="tool_call",
                    role="assistant",
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    is_untrusted=False,
                    parent_step_indices=[model_step_idx],
                )
                steps.append(tc_step)

                # Pre-execution defense check (Component D runtime guard)
                if self.defense_hook is not None:
                    defense_eval = self.defense_hook(steps, env)
                    if defense_eval.get("decision") == "block":
                        blocked_by_defense = True
                        defense_decision = "block"
                        break

                # Execute in mock environment
                result = MockToolRegistry.execute(tc.name, tc.arguments, env)

                # Determine if result contains untrusted content
                is_untrusted_result = False
                if tc.name in ("read_email", "read_document"):
                    # Content read from external email or document is inherently untrusted
                    is_untrusted_result = True

                tr_step_idx = len(steps)
                tr_step = TrajectoryStep(
                    step_index=tr_step_idx,
                    step_type="tool_result",
                    role="tool",
                    tool_name=tc.name,
                    tool_result=result,
                    is_untrusted=is_untrusted_result,
                    parent_step_indices=[tc_step_idx],
                )
                steps.append(tr_step)
                tool_result_indices.append(tr_step_idx)

                # Pass tool output back to agent context
                result_str = str(result)
                messages.append(
                    LLMMessage(
                        role="tool",
                        name=tc.name,
                        tool_call_id=tc.id,
                        content=result_str,
                        is_untrusted=is_untrusted_result,
                    )
                )

            if blocked_by_defense:
                break

            last_influencing_step_idx = tool_result_indices[-1] if tool_result_indices else model_step_idx

        # Post-execution evaluation
        duration = time.time() - start_time
        utility_eval = task.success_criteria.evaluate(initial_state, env)
        task_success = utility_eval["success"]

        # Evaluate attack success if attack goal present
        attack_success = False
        if task.metadata.get("is_attacked") and task.metadata.get("attack_goal"):
            goal_data = task.metadata["attack_goal"]
            goal = AttackGoal(
                target_tool=goal_data.get("target_tool", "send_payment"),
                target_args=goal_data.get("target_args", {}),
            )
            attack_success = goal.is_achieved(env)

        return TrajectoryRun(
            task_id=task.id,
            domain=task.domain,
            language=task.language,
            split=task.split,
            is_attacked=bool(task.metadata.get("is_attacked", False)),
            attack_id=task.metadata.get("attack_id"),
            attack_family=task.metadata.get("attack_family"),
            model_provider=self.provider_name,
            model_name=self.model_name,
            steps=steps,
            task_success=task_success,
            attack_success=attack_success,
            blocked_by_defense=blocked_by_defense,
            defense_decision=defense_decision or ("block" if blocked_by_defense else "allow"),
            execution_details={"utility": utility_eval, "audit_events": len(env.audit_log)},
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            duration_sec=duration,
        )
