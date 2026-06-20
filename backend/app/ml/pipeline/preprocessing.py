from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class PreprocessArtifacts:
    transformer: ColumnTransformer
    feature_names_out: List[str]
    selected_feature_names: List[str] = field(default_factory=list)
    feature_mappings: Dict[str, Any] = field(default_factory=dict)
    selector: Optional[Any] = None


def _normalize_list(x: List[str] | None) -> List[str]:
    return [s for s in (x or []) if s]


def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    before = len(df)
    df2 = df.drop_duplicates()
    return df2, before - len(df2)


def build_transformer(
    *,
    categorical_columns: List[str],
    numerical_columns: List[str],
    fill_missing_strategy: str,
    categorical_missing_strategy: str,
) -> ColumnTransformer:
    numerical_imputer: SimpleImputer
    if fill_missing_strategy == "median":
        numerical_imputer = SimpleImputer(strategy="median")
    elif fill_missing_strategy == "mean":
        numerical_imputer = SimpleImputer(strategy="mean")
    elif fill_missing_strategy == "zero":
        numerical_imputer = SimpleImputer(strategy="constant", fill_value=0)
    else:
        raise ValueError(
            "fill_missing_strategy must be one of: median, mean, zero. "
            f"Got {fill_missing_strategy}"
        )

    categorical_imputer = SimpleImputer(strategy="constant", fill_value=categorical_missing_strategy)

    numeric_pipeline = [
        ("imputer", numerical_imputer),
        ("scaler", StandardScaler(with_mean=True, with_std=True)),
    ]

    categorical_pipeline = [
        ("imputer", categorical_imputer),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        ),
    ]

    transformer = ColumnTransformer(
        transformers=[
            ("num", _PipelineFactory(numeric_pipeline), numerical_columns),
            ("cat", _PipelineFactory(categorical_pipeline), categorical_columns),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return transformer


class _PipelineFactory:
    """Tiny helper to avoid importing sklearn.pipeline at module import time."""

    def __init__(self, steps: list[tuple[str, Any]]):
        from sklearn.pipeline import Pipeline

        self.pipeline = Pipeline(steps)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        return self.pipeline

    def __getattr__(self, item: str) -> Any:
        # Prevent infinite recursion during unpickling
        if item == 'pipeline':
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")
        try:
            return getattr(object.__getattribute__(self, 'pipeline'), item)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")


def fit_preprocessor(
    df: pd.DataFrame,
    *,
    categorical_columns: List[str],
    numerical_columns: List[str],
    fill_missing_strategy: str,
    categorical_missing_strategy: str,
) -> PreprocessArtifacts:
    transformer = build_transformer(
        categorical_columns=categorical_columns,
        numerical_columns=numerical_columns,
        fill_missing_strategy=fill_missing_strategy,
        categorical_missing_strategy=categorical_missing_strategy,
    )

    transformer.fit(df)

    feature_names_out = list(transformer.get_feature_names_out())
    artifacts = PreprocessArtifacts(
        transformer=transformer,
        feature_names_out=feature_names_out,
        selected_feature_names=list(feature_names_out),
    )
    return artifacts


def build_feature_mappings(
    transformer: ColumnTransformer,
    categorical_columns: List[str],
    numerical_columns: List[str],
) -> Dict[str, Any]:
    mappings: Dict[str, Any] = {
        "categorical": {},
        "numerical": {
            "columns": list(numerical_columns),
            "scaler": {},
        },
    }

    for name, estimator, cols in transformer.transformers_:
        if name == "cat" and len(categorical_columns) > 0:
            encoder = estimator.named_steps["encoder"]
            for col_name, categories in zip(categorical_columns, encoder.categories_):
                mappings["categorical"][col_name] = [
                    None if v is None else (v if isinstance(v, (int, float, str)) else str(v))
                    for v in categories
                ]
        if name == "num" and len(numerical_columns) > 0:
            scaler = estimator.named_steps["scaler"]
            mappings["numerical"]["scaler"] = {
                "mean": [float(v) for v in scaler.mean_],
                "scale": [float(v) for v in scaler.scale_],
            }

    return mappings


def apply_feature_selection(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    k: int,
) -> tuple[np.ndarray, List[str], SelectKBest, Dict[str, Any]]:
    if k <= 0:
        raise ValueError("feature_selection_k must be a positive integer")

    k = min(k, len(feature_names))
    selector = SelectKBest(score_func=mutual_info_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    selected_mask = selector.get_support()
    selected_feature_names = [name for name, keep in zip(feature_names, selected_mask) if keep]

    feature_scores = [None if score is None or np.isnan(score) else float(score) for score in selector.scores_]
    selection_report = {
        "enabled": True,
        "k_requested": int(k),
        "k_selected": len(selected_feature_names),
        "selected_feature_names": selected_feature_names,
        "scores": {
            name: score
            for name, score in zip(feature_names, feature_scores)
            if score is not None
        },
    }

    return X_selected, selected_feature_names, selector, selection_report


def transform_features(df: pd.DataFrame, artifacts: PreprocessArtifacts) -> np.ndarray:
    return artifacts.transformer.transform(df)


def serialize_artifacts(path: str, artifacts: PreprocessArtifacts) -> None:
    joblib.dump(artifacts, path)


def load_artifacts(path: str) -> PreprocessArtifacts:
    return joblib.load(path)


def build_missingness_report(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    for c in columns:
        if c not in df.columns:
            continue
        na = int(df[c].isna().sum())
        report[c] = {"missing_count": na, "missing_ratio": na / max(1, len(df))}
    return report

