"""Command-line entry point for the first evaluation lessons."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .datasets import DEEPSET_DATASET_ID, DEEPSET_REVISION, load_huggingface_split
from .metrics import binary_metrics
from .runner import run_evaluation, select_sample


def _smoke() -> int:
    labels = [True, False, True, False]
    scores = [0.94, 0.08, 0.56, 0.40]
    report = {
        "mode": "offline_smoke",
        "note": "Synthetic scores only; this command makes no Jev or Hugging Face requests.",
        "metrics": binary_metrics(labels, scores),
    }
    print(json.dumps(report, indent=2))
    return 0


def _run(args: argparse.Namespace) -> int:
    model = args.model or os.getenv("JEV_MODEL", "jev-latest")
    if not os.getenv("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is required for a live run. See .env.example.", file=sys.stderr)
        return 2

    examples = load_huggingface_split(
        args.dataset,
        revision=args.revision,
        split=args.split,
        text_column=args.text_column,
        label_column=args.label_column,
    )
    sample = select_sample(examples, limit=args.limit, seed=args.seed)
    summary = run_evaluation(
        sample,
        dataset_id=args.dataset,
        revision=args.revision,
        split=args.split,
        model=model,
        output_dir=Path(args.output),
        threshold=args.threshold,
        timeout_seconds=args.timeout,
    )
    print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jev-eval")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("smoke", help="Run an offline metric smoke check with synthetic scores")

    run_parser = commands.add_parser("run", help="Evaluate a pinned Hugging Face dataset split")
    run_parser.add_argument("--dataset", default=DEEPSET_DATASET_ID)
    run_parser.add_argument("--revision", default=DEEPSET_REVISION)
    run_parser.add_argument("--split", default="test")
    run_parser.add_argument("--text-column", default="text")
    run_parser.add_argument("--label-column", default="label")
    run_parser.add_argument("--limit", type=int, default=8)
    run_parser.add_argument("--seed", type=int, default=42)
    run_parser.add_argument("--model")
    run_parser.add_argument("--threshold", type=float, default=0.5)
    run_parser.add_argument("--timeout", type=float, default=10.0)
    run_parser.add_argument("--output", default="results/runs/deepset-pilot")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "smoke":
        return _smoke()
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())