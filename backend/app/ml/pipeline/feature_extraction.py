from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class FeatureExtractionResult:
    feature_df: pd.DataFrame
    feature_selection_columns: List[str]
    extraction_report: Dict[str, Any]


def _safe_split_ip_column(series: pd.Series) -> pd.DataFrame:
    """For future use: split IP strings if dataset provides separate octets.

    For now we keep as is.
    """

    return pd.DataFrame({series.name: series})


def basic_feature_extraction(
    df: pd.DataFrame,
    *,
    label_column: str,
    ignore_columns: List[str],
    enable_feature_selection: bool,
    feature_selection_k: int,
) -> FeatureExtractionResult:
    """Dataset-agnostic feature extraction.

    For this phase we focus on:
    - removing ignore columns
    - removing duplicates already handled earlier (but safe here)
    - selecting candidate feature columns

    Deeper extraction (PCA/packet-level/flow-level derived stats) depends on
    dataset schema. Those hooks will be added in later phases.
    """

    ignore_set = set(ignore_columns or [])
    ignore_set.add(label_column)

    candidate_cols = [c for c in df.columns if c not in ignore_set]
    # Try to drop all-null columns (common in custom dumps)
    non_empty_cols = [c for c in candidate_cols if df[c].notna().any()]

    extraction_report: Dict[str, Any] = {
        "candidate_feature_columns": len(candidate_cols),
        "non_empty_feature_columns": len(non_empty_cols),
        "dropped_all_null_columns": sorted(set(candidate_cols) - set(non_empty_cols)),
    }

    feature_df = df[non_empty_cols].copy()

    # Feature selection hook (optional): we keep it for later extension.
    # In this phase, actual selection should occur after encoding/scaling.
    # We'll mark which columns are eligible.
    selected_cols = list(feature_df.columns)
    if enable_feature_selection:
        extraction_report["feature_selection"] = {
            "enabled": True,
            "method": "deferred_to_post_encoding",
            "k": feature_selection_k,
        }
    else:
        extraction_report["feature_selection"] = {"enabled": False}

    return FeatureExtractionResult(
        feature_df=feature_df,
        feature_selection_columns=selected_cols,
        extraction_report=extraction_report,
    )

