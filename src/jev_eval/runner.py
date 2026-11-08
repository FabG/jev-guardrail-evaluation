"""Run pinned dataset examples and persist resumable, text-free results."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .datasets import Example
from .metrics import binary_metrics, latency_metrics


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    cached = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            cached[record["example_id"]] = record
    return cached


def _make_evaluator(model: str, timeout_seconds: float):
    from .jev import JevEvaluator

    return JevEvaluator(model, timeout_seconds=timeout_seconds)


def select_sample(examples: list[Example], *, limit: int | None, seed: int) -> list[Example]:
    if limit is None or limit >= len(examples):
        return examples
    if limit < 1:
        raise ValueError("limit must be at least 1")
    return random.Random(seed).sample(examples, limit)


def run_evaluation(
    examples: list[Example],
    *,
    dataset_id: str,
    revision: str,
    split: str,
    model: str,
    output_dir: Path,
    threshold: float = 0.5,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.jsonl"
    from .jev import INJECTION_QUESTION

    question_hash = _sha256(INJECTION_QUESTION)
    existing = _read_cache(predictions_path)
    identity = {"dataset_id": dataset_id, "revision": revision, "split": split, "model": model}
    reusable = {}
    for example in examples:
        record = existing.get(example.example_id)
        if (
            record is not None
            and all(record.get(key) == value for key, value in identity.items())
            and record.get("question_sha256") == question_hash
            and record.get("content_sha256") == _sha256(example.text)
        ):
            reusable[example.example_id] = record

    records: list[dict[str, Any]] = []
    pending = [example for example in examples if example.example_id not in reusable]
    if pending:
        with (
            predictions_path.open("a", encoding="utf-8") as destination,
            _make_evaluator(model, timeout_seconds) as evaluator,
        ):
            for example in pending:
                result = evaluator.evaluate(example.text)
                record = {
                    **identity,
                    "example_id": example.example_id,
                    "content_sha256": _sha256(example.text),
                    "label_is_injection": example.is_injection,
                    "score": result.score,
                    "latency_ms": result.latency_ms,
                    "resolved_model": result.model,
                    "input_tokens": result.input_tokens,
                    "question_sha256": question_hash,
                }
                destination.write(json.dumps(record, sort_keys=True) + "\n")
                destination.flush()
                reusable[example.example_id] = record

    records = [reusable[example.example_id] for example in examples]
    scores = [float(record["score"]) for record in records]
    labels = [bool(record["label_is_injection"]) for record in records]
    latencies = [float(record["latency_ms"]) for record in records]
    resolved_models = sorted({str(record["resolved_model"]) for record in records})
    summary = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        **identity,
        "question_sha256": question_hash,
        "resolved_models": resolved_models,
        "metrics": binary_metrics(labels, scores, threshold=threshold),
        "provider_latency": latency_metrics(latencies),
        "latency_target_ms": 200,
        "provider_p95_under_target": (
            latency_metrics(latencies)["p95_ms"] < 200 if latencies else None
        ),
        "text_persisted": False,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary