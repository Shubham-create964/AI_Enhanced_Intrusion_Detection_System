from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.ml.pipeline.config import PipelineConfig, build_output_paths
from app.ml.pipeline.data_loaders import ensure_columns_exist, load_csv
from app.ml.pipeline.feature_extraction import basic_feature_extraction
from app.ml.pipeline.preprocessing import (
    PreprocessArtifacts,
    apply_feature_selection,
    build_feature_mappings,
    build_missingness_report,
    fit_preprocessor,
    remove_duplicates,
    serialize_artifacts,
    transform_features,
)
from app.ml.pipeline.splitting import split_dataset


def _parse_columns(csv_columns: List[str] | None) -> List[str]:
    return [c for c in (csv_columns or []) if c]


def _coerce_numeric_columns(df: pd.DataFrame, numerical_columns: List[str]) -> pd.DataFrame:
    """Best-effort numeric coercion."""
    out = df.copy()
    for c in numerical_columns:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def run_phase2_pipeline(cfg: PipelineConfig) -> Dict[str, Any]:
    paths = build_output_paths(cfg)
    for p in [paths["splits"], paths["artifacts"], paths["reports"], paths["base"]]:
        p.mkdir(parents=True, exist_ok=True)

    df = load_csv(cfg.input_file)
    ensure_columns_exist(df, [cfg.label_column], context="label")

    # Normalize user-provided column lists
    categorical_columns = _parse_columns(cfg.categorical_columns)
    numerical_columns = _parse_columns(cfg.numerical_columns)
    ignore_columns = _parse_columns(cfg.ignore_columns)

    # Validate specified columns exist (ignore columns are optional, but if provided and missing, warn)
    if categorical_columns:
        ensure_columns_exist(df, categorical_columns, context="categorical")
    if numerical_columns:
        ensure_columns_exist(df, numerical_columns, context="numerical")

    # Remove duplicates early
    dup_report: Dict[str, Any] = {}
    if cfg.drop_duplicates:
        df, dup_removed = remove_duplicates(df)
        dup_report = {"drop_duplicates": True, "duplicates_removed": int(dup_removed)}
    else:
        dup_report = {"drop_duplicates": False}

    # Coerce numerical columns
    df = _coerce_numeric_columns(df, numerical_columns)

    # Reports
    all_report_columns = [c for c in (categorical_columns + numerical_columns) if c in df.columns]
    missingness_report = build_missingness_report(df, all_report_columns)

    # Feature extraction (dataset-agnostic placeholder: drop ignore/all-null)
    extraction = basic_feature_extraction(
        df,
        label_column=cfg.label_column,
        ignore_columns=ignore_columns,
        enable_feature_selection=cfg.enable_feature_selection,
        feature_selection_k=cfg.feature_selection_k,
    )
    df_features = extraction.feature_df

    # Decide final feature columns.
    # Use user-provided categorical/numerical columns if present.
    # Otherwise infer from non-ignored extracted features.
    ignore_set = set(ignore_columns + [cfg.label_column])

    if not categorical_columns and not numerical_columns:
        inferred_cats: List[str] = []
        inferred_nums: List[str] = []
        for c in df_features.columns:
            if c in ignore_set:
                continue
            if pd.api.types.is_numeric_dtype(df_features[c]):
                inferred_nums.append(c)
            else:
                inferred_cats.append(c)
        categorical_columns = inferred_cats
        numerical_columns = inferred_nums
    else:
        categorical_columns = [c for c in categorical_columns if c not in ignore_set]
        numerical_columns = [c for c in numerical_columns if c not in ignore_set]

    # Fit preprocessor on candidate feature columns only.
    artifacts: PreprocessArtifacts = fit_preprocessor(
        df_features,
        categorical_columns=categorical_columns,
        numerical_columns=numerical_columns,
        fill_missing_strategy=cfg.fill_missing_strategy,
        categorical_missing_strategy=cfg.categorical_missing_strategy,
    )

    # Transform features for persistence.
    X = transform_features(df_features, artifacts)
    y = df[cfg.label_column].values

    feature_selection_report: Dict[str, Any] = {"enabled": False}
    if cfg.enable_feature_selection:
        X, selected_feature_names, selector, feature_selection_report = apply_feature_selection(
            X,
            y,
            artifacts.feature_names_out,
            cfg.feature_selection_k,
        )
        artifacts.selected_feature_names = selected_feature_names
        artifacts.selector = selector
        artifacts.feature_names_out = selected_feature_names

    # Persist transformed features as dense matrix via DataFrame
    feature_df = pd.DataFrame(X, columns=artifacts.feature_names_out)
    feature_df[cfg.label_column] = y

    # Feature mapping artifact for transparency and model serving.
    feature_mappings = build_feature_mappings(
        artifacts.transformer,
        categorical_columns=categorical_columns,
        numerical_columns=numerical_columns,
    )
    feature_mappings["selected_feature_names"] = artifacts.feature_names_out
    if cfg.enable_feature_selection:
        feature_mappings["feature_selection"] = feature_selection_report

    with open(paths["feature_mappings"], "w", encoding="utf-8") as f:
        json.dump(feature_mappings, f, indent=2)

    # Split
    split_res = split_dataset(
        feature_df,
        label_column=cfg.label_column,
        test_size=cfg.test_size,
        val_size=cfg.val_size,
        random_state=cfg.random_state,
    )

    # Persist splits
    for split_name, split_df in split_res.splits.items():
        out_parquet = paths["splits"] / f"{split_name}.parquet"
        out_csv = paths["splits"] / f"{split_name}.csv"
        split_df.to_parquet(out_parquet, index=False)
        split_df.to_csv(out_csv, index=False)

    # Artifacts
    serialize_artifacts(str(paths["preprocessors"]), artifacts)

    # Metadata & reports
    dataset_statistics = {
        "rows_total": int(len(df)),
        "features_encoded": int(len(artifacts.feature_names_out)),
        "categorical_columns_used": categorical_columns,
        "numerical_columns_used": numerical_columns,
        "ignore_columns": ignore_columns,
        "duplicates_report": dup_report,
        "feature_extraction_report": extraction.extraction_report,
        "split_counts": split_res.counts,
        "label_distribution": split_res.label_distribution,
    }

    preprocessing_report = {
        "missingness_report": missingness_report,
        "fill_missing_strategy": cfg.fill_missing_strategy,
        "categorical_missing_strategy": cfg.categorical_missing_strategy,
        "onehot_unknown": "ignore",
        "scaler": "StandardScaler",
        "feature_selection": feature_selection_report,
    }

    metadata = {
        "pipeline_config": {
            "input_file": str(cfg.input_file),
            "output_dir": str(cfg.output_dir),
            "dataset_name": cfg.dataset_name,
            "run_id": cfg.run_id,
            "label_column": cfg.label_column,
            "categorical_columns": cfg.categorical_columns,
            "numerical_columns": cfg.numerical_columns,
            "ignore_columns": cfg.ignore_columns,
            "test_size": cfg.test_size,
            "val_size": cfg.val_size,
            "random_state": cfg.random_state,
            "drop_duplicates": cfg.drop_duplicates,
            "fill_missing_strategy": cfg.fill_missing_strategy,
            "categorical_missing_strategy": cfg.categorical_missing_strategy,
            "enable_feature_selection": cfg.enable_feature_selection,
            "feature_selection_k": cfg.feature_selection_k,
        },
        "dataset_statistics": dataset_statistics,
        "reports": {
            "preprocessing_report": preprocessing_report,
            "dataset_statistics": dataset_statistics,
        },
        "artifacts": {
            "preprocessors_joblib": str(paths["preprocessors"]),
            "features_schema_json": str(paths["features_schema"]),
            "feature_mappings_json": str(paths["feature_mappings"]),
        },
    }

    with open(paths["metadata"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    features_schema = {
        "label_column": cfg.label_column,
        "feature_names_out": artifacts.feature_names_out,
        "num_features": int(len(artifacts.feature_names_out)),
    }
    with open(paths["features_schema"], "w", encoding="utf-8") as f:
        json.dump(features_schema, f, indent=2)

    with open(paths["preprocess_report"], "w", encoding="utf-8") as f:
        json.dump(preprocessing_report, f, indent=2)

    with open(paths["dataset_report"], "w", encoding="utf-8") as f:
        json.dump(dataset_statistics, f, indent=2)

    return metadata

