"""Load and normalize public prompt-injection datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEEPSET_DATASET_ID = "deepset/prompt-injections"
DEEPSET_REVISION = "4f61ecb038e9c3fb77e21034b22511b523772cdd"


@dataclass(frozen=True)
class Example:
    example_id: str
    text: str
    is_injection: bool


def normalize_label(value: Any, label_names: list[str] | None = None) -> bool:
    """Return whether a dataset label denotes an injection; reject unknown labels."""
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if label_names is not None:
            try:
                value = label_names[value]
            except IndexError as error:
                raise ValueError(f"Label index {value} is outside the dataset label names") from error
        elif value in (0, 1):
            return value == 1
        else:
            raise ValueError(f"Unsupported numeric label: {value}")

    normalized = str(value).strip().casefold()
    if normalized in {
        "1",
        "attack",
        "injection",
        "prompt_injection",
        "prompt-injection",
        "malicious",
        "unsafe",
        "positive",
    }:
        return True
    if normalized in {
        "0",
        "benign",
        "clean",
        "no_injection",
        "no-injection",
        "normal",
        "safe",
        "negative",
    }:
        return False
    raise ValueError(f"Unsupported injection label: {value!r}")


def normalize_rows(
    rows: list[dict[str, Any]],
    *,
    dataset_id: str,
    split: str,
    text_column: str = "text",
    label_column: str = "label",
    label_names: list[str] | None = None,
) -> list[Example]:
    examples = []
    for row_index, row in enumerate(rows):
        try:
            text = row[text_column]
            label = row[label_column]
        except KeyError as error:
            raise ValueError(f"Dataset is missing required column: {error.args[0]}") from error
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Row {row_index} has empty or non-text content")
        examples.append(
            Example(
                example_id=f"{dataset_id}:{split}:{row_index}",
                text=text,
                is_injection=normalize_label(label, label_names),
            )
        )
    return examples


def load_huggingface_split(
    dataset_id: str,
    *,
    revision: str,
    split: str,
    text_column: str = "text",
    label_column: str = "label",
) -> list[Example]:
    """Download a pinned Hub split and normalize its text and binary labels."""
    from datasets import load_dataset

    dataset = load_dataset(dataset_id, split=split, revision=revision)
    features = getattr(dataset, "features", {})
    label_feature = features.get(label_column)
    label_names = getattr(label_feature, "names", None)
    return normalize_rows(
        list(dataset),
        dataset_id=dataset_id,
        split=split,
        text_column=text_column,
        label_column=label_column,
        label_names=label_names,
    )