#!/usr/bin/env python3
"""CLI benchmark execution runner for AgentGuard-IN."""

import argparse
import os
import sys
from pathlib import Path

# Add src to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from agentguard.agents.agent_loop import AgentRunner
from agentguard.agents.llm_client import get_llm_client
from agentguard.attacks.injector import AttackInjector
from agentguard.attacks.templates import get_default_attack_templates
from agentguard.eval.metrics import compute_benchmark_metrics
from agentguard.logging.jsonl_logger import TrajectoryLogger
from agentguard.tasks.generator import generate_phase1_tasks


def main():
    parser = argparse.ArgumentParser(description="Run AgentGuard-IN Benchmark")
    parser.add_argument("--provider", type=str, default="mock", help="LLM Provider (mock, gemini, openai, ollama, huggingface)")
    parser.add_argument("--model", type=str, default=None, help="Model name identifier")
    parser.add_argument("--mock_mode", type=str, default="vulnerable", choices=["vulnerable", "robust"], help="Mode for mock LLM")
    parser.add_argument("--tasks", type=int, default=5, help="Number of benchmark tasks to run")
    parser.add_argument("--mode", type=str, default="both", choices=["clean", "attacked", "both"], help="Run clean, attacked, or both")
    parser.add_argument("--output_log", type=str, default="data/runs/phase1_runs.jsonl", help="JSONL log file path")
    parser.add_argument("--config_dir", type=str, default="configs", help="Path to config directory")
    args = parser.parse_args()

    # Read budget config
    budget_file = Path(args.config_dir) / "budget.yaml"
    budget_config = {}
    if budget_file.exists():
        with open(budget_file, "r", encoding="utf-8") as f:
            budget_config = yaml.safe_load(f)

    # Estimate cost and count runs (Rule 11)
    planned_runs = args.tasks if args.mode in ("clean", "attacked") else args.tasks * 2
    est_cost = 0.0
    model_key = args.model or ("mock-llm" if args.provider == "mock" else "gemini-1.5-flash")
    cost_in = budget_config.get("cost_per_1k_input_tokens", {}).get(model_key, 0.0)
    cost_out = budget_config.get("cost_per_1k_output_tokens", {}).get(model_key, 0.0)
    est_cost = planned_runs * (cost_in * 0.5 + cost_out * 0.1)

    print("=================================================================")
    print("AgentGuard-IN: Benchmark Run Execution")
    print(f"Provider: {args.provider} | Model: {args.model or 'default'} | Mock Mode: {args.mock_mode}")
    print(f"Planned Runs: {planned_runs} ({args.mode}) | Est. Cost: ${est_cost:.4f} USD")
    print("=================================================================")

    # Initialize LLM Client
    client = get_llm_client(provider=args.provider, model_name=args.model, mode=args.mock_mode)
    runner = AgentRunner(
        llm_client=client,
        provider_name=args.provider,
        model_name=args.model or f"{args.provider}-default",
    )

    # Prepare Tasks
    all_tasks = generate_phase1_tasks()
    selected_tasks = all_tasks[: args.tasks]

    # Initialize Attack Injector
    templates = get_default_attack_templates()
    injector = AttackInjector(templates=templates)

    # Setup Logger
    log_path = Path(args.output_log)
    logger = TrajectoryLogger(log_path)

    completed_runs = []

    # Execute Runs
    for idx, task in enumerate(selected_tasks):
        # 1. Clean run
        if args.mode in ("clean", "both"):
            print(f"[{idx+1}/{len(selected_tasks)}] Running CLEAN task {task.id} ({task.domain})...", end=" ", flush=True)
            clean_run = runner.run_task(task)
            logger.log_run(clean_run)
            completed_runs.append(clean_run)
            status = "SUCCESS" if clean_run.task_success else "FAILED"
            print(f"-> {status} (Utility: {clean_run.task_success})")

        # 2. Attacked run
        if args.mode in ("attacked", "both"):
            # Select template deterministically cycling through families
            template = templates[idx % len(templates)]
            if task.untrusted_slots:
                attacked_task = injector.inject(task, template)
                print(f"[{idx+1}/{len(selected_tasks)}] Running ATTACKED task {task.id} (Family: {template.family})...", end=" ", flush=True)
                attacked_run = runner.run_task(attacked_task)
                logger.log_run(attacked_run)
                completed_runs.append(attacked_run)
                asr_status = "EXPLOITED" if attacked_run.attack_success else "DEFENDED"
                print(f"-> {asr_status} (Utility: {attacked_run.task_success}, ASR: {attacked_run.attack_success})")
            else:
                print(f"[{idx+1}/{len(selected_tasks)}] Skipping attack for {task.id} (No untrusted slot)")

    # Compute and report metrics
    metrics = compute_benchmark_metrics(completed_runs)
    print("\n" + "=" * 65)
    print("BENCHMARK METRICS SUMMARY REPORT")
    print("=" * 65)
    print(metrics.to_markdown_table())
    print("=" * 65)
    print(f"Run trajectories saved to: {log_path.resolve()}\n")


if __name__ == "__main__":
    main()
