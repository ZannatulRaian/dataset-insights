"""A tiny in-memory dataset store.

Uploaded DataFrames are kept in memory, keyed by a generated dataset id.
This keeps the project simple (no database). The oldest datasets are
evicted once MAX_DATASETS is reached so memory cannot grow forever.
"""
from collections import OrderedDict
from uuid import uuid4

import pandas as pd

MAX_DATASETS = 20

_datasets: "OrderedDict[str, dict]" = OrderedDict()


def save_dataset(df: pd.DataFrame, filename: str) -> str:
    dataset_id = uuid4().hex[:12]
    _datasets[dataset_id] = {"df": df, "filename": filename}
    while len(_datasets) > MAX_DATASETS:
        _datasets.popitem(last=False)
    return dataset_id


def get_dataset(dataset_id: str):
    """Return the stored entry or None."""
    return _datasets.get(dataset_id)


def clear() -> None:
    _datasets.clear()
