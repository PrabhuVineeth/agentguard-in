#!/usr/bin/env python3
"""Execute scaled benchmark runs with resume, prompt caching, and cost tracking."""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from agentguard.agents.agent_loop import AgentRunner
from agentguard.agents.llm_client import get_llm_client
from agentguard.eval.metrics import compute_benchmark_metrics
from agentguard.logging.jsonl_logger import TrajectoryLogger
from agentguard.logging.schema import TrajectoryRun
from agentguard.tasks.generator import load_tasks_from_disk
from agentguard.tasks.schema import BenchmarkTask


class CachedLLMClient:
    """Wraps an LLM client with file-based MD5 response caching to eliminate redundant costs."""

    def __init__(self, client, cache_dir: Path, enabled: bool = True):
        self.client = client
        self.cache_dir = cache_dir
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash_request(self, messages, tools) -> str:
        payload = {
            "messages": [m.model_dump() for m in messages],
            "tools": tools,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def generate(self, messages, tools=None, **kwargs):
        if not self.enabled:
            return self.client.generate(messages, tools, **kwargs)

        req_hash = self._hash_request(messages, tools)
        cache_file = self.cache_dir / f"{req_hash}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    from agentguard.agents.llm_client import LLMResponse
                    return LLMResponse.model_validate_json(f.read())
            except Exception:
                pass

        resp = self.client.generate(messages, tools, **kwargs)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(resp.model_dump_json())
        except Exception:
            pass

        return resp


def main():
    parser = argparse.ArgumentParser(description="Scaled AgentGuard-IN Benchmark Runner")
    parser.add_argument("--model1_provider", type=str, default="mock", help="First model provider")
    parser.add_argument("--model1_mode", type=str, default="vulnerable", help="Mode for model 1 (vulnerable)")
    parser.add_argument("--model2_provider", type=str, default="mock", help="Second model provider")
    parser.add_argument("--model2_mode", type=str, default="robust", help="Mode for model 2 (robust/aligned)")
    parser.add_argument("--max_runs", type=int, default=500, help="Maximum number of attacked runs to execute per model")
    parser.add_argument("--output_log", type=str, default="data/runs/scaled_benchmark_runs.jsonl")
    parser.add_argument("--cache_dir", type=str, default="data/cache")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume execution if partial log exists")
    args = parser.parse_args()

    data_dir = Path(__file__).resolve().parent.parent / "data"
    attacks_file = data_dir / "attacks_benchmark.json"
    clean_tasks_file = data_dir / "tasks_benchmark.json"

    if not attacks_file.exists() or not clean_tasks_file.exists():
        print("Dataset files missing. Running generate_scaled_dataset.py first...")
        from scripts.generate_scaled_dataset import build_scaled_dataset
        build_scaled_dataset()

    attacked_tasks = load_tasks_from_disk(attacks_file)
    clean_tasks = load_tasks_from_disk(clean_tasks_file)

    log_path = Path(args.output_log)
    logger = TrajectoryLogger(log_path)

    # 1. Load completed run keys for resume capability
    completed_keys = set()
    if args.resume and log_path.exists():
        existing_runs = logger.read_runs()
        for r in existing_runs:
            completed_keys.add(f"{r.model_provider}_{r.model_name}_{r.task_id}_{r.is_attacked}")
        print(f"Resume active: Found {len(completed_keys)} previously completed runs in {log_path.name}")

    # 2. Configure Model 1 and Model 2
    models_to_test = [
        {"provider": args.model1_provider, "mode": args.model1_mode, "label": f"{args.model1_provider}_{args.model1_mode}"},
        {"provider": args.model2_provider, "mode": args.model2_mode, "label": f"{args.model2_provider}_{args.model2_mode}"},
    ]

    cache_path = Path(args.cache_dir)
    all_runs: List[TrajectoryRun] = []

    print("\n" + "=" * 70)
    print("EXECUTING SCALED BENCHMARK ACROSS 2 MODEL CONFIGURATIONS")
    print(f"Total Attacked Available: {len(attacked_tasks)} | Execution Target: {args.max_runs} per model")
    print("=" * 70)

    for m_cfg in models_to_test:
        raw_client = get_llm_client(provider=m_cfg["provider"], mode=m_cfg["mode"])
        cached_client = CachedLLMClient(raw_client, cache_dir=cache_path / m_cfg["label"])
        runner = AgentRunner(
            llm_client=cached_client,
            provider_name=m_cfg["provider"],
            model_name=m_cfg["label"],
        )

        print(f"\n---> Commencing evaluation for: {m_cfg['label']}")
        model_runs = []
        executed_count = 0

        # Run subset of clean tasks for baseline utility check
        for c_task in clean_tasks[:30]:
            run_key = f"{m_cfg['provider']}_{m_cfg['label']}_{c_task.id}_False"
            if run_key in completed_keys:
                continue
            run = runner.run_task(c_task)
            logger.log_run(run)
            completed_keys.add(run_key)
            model_runs.append(run)

        # Run attacked tasks
        for a_task in attacked_tasks[: args.max_runs]:
            run_key = f"{m_cfg['provider']}_{m_cfg['label']}_{a_task.id}_True"
            if run_key in completed_keys:
                continue

            run = runner.run_task(a_task)
            logger.log_run(run)
            completed_keys.add(run_key)
            model_runs.append(run)
            executed_count += 1

            if executed_count % 100 == 0:
                print(f"  [{m_cfg['label']}] Progress: {executed_count}/{min(args.max_runs, len(attacked_tasks))} attacked tasks...")

        # Read all runs for this model from log
        all_logged = [r for r in logger.read_runs() if r.model_name == m_cfg["label"]]
        metrics = compute_benchmark_metrics(all_logged)

        print(f"\n--- Model Summary: {m_cfg['label']} ---")
        print(f"Evaluated Runs: {metrics.total_runs} (Clean: {metrics.clean_runs}, Attacked: {metrics.attacked_runs})")
        print(f"Benign Utility (Clean): {metrics.utility * 100:.1f}%")
        print(f"Attack Success Rate (ASR): {metrics.asr * 100:.1f}%")
        print(f"False-Block Rate: {metrics.false_block_rate * 100:.1f}%")
        all_runs.extend(all_logged)

    # Print overall comparison table
    print("\n" + "=" * 70)
    print("PHASE 2 MULTI-MODEL SCALED BENCHMARK RESULTS")
    print("=" * 70)
    for m_cfg in models_to_test:
        sub = [r for r in all_runs if r.model_name == m_cfg["label"]]
        if sub:
            sm = compute_benchmark_metrics(sub)
            print(f"Model: {m_cfg['label']}")
            print(sm.to_markdown_table())
            print("-" * 50)


if __name__ == "__main__":
    main()
