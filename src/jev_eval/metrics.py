"""Dependency-free binary classification and latency summaries."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def binary_metrics(
    labels: Sequence[bool], scores: Sequence[float], *, threshold: float = 0.5
) -> dict[str, Any]:
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have the same length")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if any(not 0 <= score <= 1 for score in scores):
        raise ValueError("all scores must be between 0 and 1")

    true_positive = sum(label and score >= threshold for label, score in zip(labels, scores))
    false_positive = sum(not label and score >= threshold for label, score in zip(labels, scores))
    true_negative = sum(not label and score < threshold for label, score in zip(labels, scores))
    false_negative = sum(label and score < threshold for label, score in zip(labels, scores))
    total = len(labels)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    benign_count = true_negative + false_positive

    return {
        "count": total,
        "threshold": threshold,
        "accuracy": (true_positive + true_negative) / total if total else None,
        "precision": precision if total else None,
        "recall": recall if total else None,
        "f1": f1 if total else None,
        "false_block_rate": false_positive / benign_count if benign_count else None,
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
    }


def latency_metrics(latencies_ms: Sequence[float]) -> dict[str, float | int | None]:
    return {
        "count": len(latencies_ms),
        "p50_ms": percentile(latencies_ms, 0.50),
        "p95_ms": percentile(latencies_ms, 0.95),
        "p99_ms": percentile(latencies_ms, 0.99),
        "max_ms": max(latencies_ms) if latencies_ms else None,
    }