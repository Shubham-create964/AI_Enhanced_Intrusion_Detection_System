from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass
class SplitResult:
    splits: Dict[str, pd.DataFrame]
    counts: Dict[str, int]
    label_distribution: Dict[str, Dict[str, int]]


def _label_dist(df: pd.DataFrame, label_column: str) -> Dict[str, int]:
    vc = df[label_column].value_counts(dropna=False)
    return {str(k): int(v) for k, v in vc.items()}


def split_dataset(
    df: pd.DataFrame,
    *,
    label_column: str,
    test_size: float,
    val_size: float,
    random_state: int,
) -> SplitResult:
    if label_column not in df.columns:
        raise ValueError(f"label_column '{label_column}' not present in dataset")

    if not (0 < test_size < 1):
        raise ValueError("test_size must be between 0 and 1")
    if not (0 < val_size < 1):
        raise ValueError("val_size must be between 0 and 1")

    if test_size + val_size >= 1:
        raise ValueError("val_size + test_size must be < 1")

    y = df[label_column]

    train_df, temp_df = train_test_split(
        df,
        test_size=(test_size + val_size),
        stratify=y,
        random_state=random_state,
    )

    # Now temp_df split into val/test. val_size is relative to full, so val_ratio_of_temp = val_size/(val+test)
    val_ratio_of_temp = val_size / (test_size + val_size)

    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - val_ratio_of_temp),
        stratify=temp_df[label_column],
        random_state=random_state,
    )

    splits = {"train": train_df, "val": val_df, "test": test_df}
    counts = {k: int(len(v)) for k, v in splits.items()}
    label_distribution = {k: _label_dist(v, label_column) for k, v in splits.items()}

    return SplitResult(splits=splits, counts=counts, label_distribution=label_distribution)

