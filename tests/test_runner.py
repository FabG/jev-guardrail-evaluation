import json

from jev_eval.datasets import Example
from jev_eval.jev import JevResult
from jev_eval.runner import run_evaluation, select_sample


def test_select_sample_is_seeded_and_bounded():
    examples = [Example(str(index), f"prompt {index}", bool(index % 2)) for index in range(10)]
    first = select_sample(examples, limit=4, seed=42)
    second = select_sample(examples, limit=4, seed=42)
    assert first == second
    assert len(first) == 4


def test_run_persists_hashes_not_prompt_text_and_reuses_cache(tmp_path, monkeypatch):
    calls = []

    class FakeEvaluator:
        def __init__(self, model, *, timeout_seconds):
            calls.append(("init", model, timeout_seconds))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def evaluate(self, text):
            calls.append(("evaluate", text))
            return JevResult(0.9, 42.0, "jev-test", 10)

    monkeypatch.setattr(
        "jev_eval.runner._make_evaluator",
        lambda model, timeout_seconds: FakeEvaluator(model, timeout_seconds=timeout_seconds),
    )
    examples = [Example("source:test:0", "private prompt text", True)]
    kwargs = {
        "dataset_id": "source/dataset",
        "revision": "abc123",
        "split": "test",
        "model": "jev-test",
        "output_dir": tmp_path,
    }
    summary = run_evaluation(examples, **kwargs)

    prediction = (tmp_path / "predictions.jsonl").read_text(encoding="utf-8")
    assert "private prompt text" not in prediction
    assert "content_sha256" in prediction
    assert summary["provider_latency"]["p50_ms"] == 42.0
    assert summary["text_persisted"] is False
    assert len([call for call in calls if call[0] == "evaluate"]) == 1

    def fail_if_initialized(*_args, **_kwargs):
        raise AssertionError("A fully cached run must not initialize the Jev client")

    monkeypatch.setattr("jev_eval.runner._make_evaluator", fail_if_initialized)
    resumed = run_evaluation(examples, **kwargs)
    assert resumed["metrics"] == summary["metrics"]
    assert len((tmp_path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_content_change_invalidates_cached_score(tmp_path, monkeypatch):
    calls = []

    class FakeEvaluator:
        def __init__(self, model, *, timeout_seconds):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def evaluate(self, text):
            calls.append(text)
            return JevResult(0.4, 25.0, "jev-test", 8)

    monkeypatch.setattr(
        "jev_eval.runner._make_evaluator",
        lambda model, timeout_seconds: FakeEvaluator(model, timeout_seconds=timeout_seconds),
    )
    kwargs = {
        "dataset_id": "source/dataset",
        "revision": "abc123",
        "split": "test",
        "model": "jev-test",
        "output_dir": tmp_path,
    }
    run_evaluation([Example("row-1", "version one", False)], **kwargs)
    run_evaluation([Example("row-1", "version two", False)], **kwargs)
    assert calls == ["version one", "version two"]

    records = [
        json.loads(line)
        for line in (tmp_path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 2