import pytest

from jev_eval.metrics import binary_metrics, latency_metrics, percentile


def test_binary_metrics_calculates_confusion_and_rates():
    report = binary_metrics([True, False, True, False], [0.9, 0.8, 0.4, 0.1])
    assert report["confusion_matrix"] == {
        "true_positive": 1,
        "false_positive": 1,
        "true_negative": 1,
        "false_negative": 1,
    }
    assert report["accuracy"] == 0.5
    assert report["false_block_rate"] == 0.5


def test_binary_metrics_handles_empty_inputs():
    report = binary_metrics([], [])
    assert report["count"] == 0
    assert report["accuracy"] is None


def test_binary_metrics_rejects_mismatched_inputs():
    with pytest.raises(ValueError, match="same length"):
        binary_metrics([True], [])


def test_percentile_uses_nearest_rank():
    assert percentile([30, 10, 20], 0.5) == 20
    assert percentile([30, 10, 20], 0.95) == 30


def test_latency_metrics_empty_and_nonempty():
    assert latency_metrics([])["p95_ms"] is None
    assert latency_metrics([10, 20, 30])["p50_ms"] == 20