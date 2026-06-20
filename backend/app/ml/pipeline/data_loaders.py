from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv(input_file: Path) -> pd.DataFrame:
    """Load a dataset from CSV.

    Note: We rely on pandas' dtype inference; later preprocessing will coerce.
    """

    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    df = pd.read_csv(input_file)
    if df.empty:
        raise ValueError("Input dataset is empty.")
    return df


def ensure_columns_exist(df: pd.DataFrame, columns: list[str], *, context: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for {context}: {missing}")

