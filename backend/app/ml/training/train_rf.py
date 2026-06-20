from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.preprocessing import LabelEncoder


@dataclass(frozen=True)
class RFTrainingConfig:
    n_estimators: int = 300
    max_depth: Optional[int] = None
    random_state: int = 42
    n_jobs: int = -1


@dataclass(frozen=True)
class TrainingArtifacts:
    model_path: Path
    metrics_path: Path
    metadata_path: Path


def _ensure_xy(df: pd.DataFrame, label_column: str) -> Tuple[np.ndarray, np.ndarray, list[str]]:
    if label_column not in df.columns:
        raise ValueError(f"label column '{label_column}' not found in dataframe")

    feature_cols = [c for c in df.columns if c != label_column]
    X = df[feature_cols].to_numpy()
    y = df[label_column].to_numpy()
    return X, y, feature_cols


def _normalize_class_labels(y: np.ndarray) -> tuple[np.ndarray, LabelEncoder]:
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    return y_enc, le


def _metrics_bundle(y_true: np.ndarray, y_pred: np.ndarray, average: str = "weighted") -> Dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def train_random_forest(
    *,
    train_path: Path,
    val_path: Path,
    test_path: Path,
    label_column: str,
    out_dir: Path,
    config: RFTrainingConfig = RFTrainingConfig(),
    run_id: Optional[str] = None,
) -> TrainingArtifacts:
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    X_train, y_train_raw, feature_cols = _ensure_xy(train_df, label_column)
    X_val, y_val_raw, _ = _ensure_xy(val_df, label_column)
    X_test, y_test_raw, _ = _ensure_xy(test_df, label_column)

    # Encode labels so model can handle string/float mixtures consistently.
    y_train_enc, le = _normalize_class_labels(y_train_raw)
    # Important: apply same encoder to val/test.
    y_val_enc = le.transform(y_val_raw)
    y_test_enc = le.transform(y_test_raw)

    model = RandomForestClassifier(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
    )

    model.fit(X_train, y_train_enc)

    val_pred = model.predict(X_val)
    test_pred = model.predict(X_test)

    # Choose best by val F1 (weighted).
    val_metrics = _metrics_bundle(y_val_enc, val_pred, average="weighted")
    test_metrics = _metrics_bundle(y_test_enc, test_pred, average="weighted")

    # Persist artifacts
    model_path = out_dir / "model.joblib"
    metrics_path = out_dir / "metrics.json"
    metadata_path = out_dir / "training_metadata.json"

    joblib.dump(
        {
            "model": model,
            "label_encoder": le,
            "feature_columns": feature_cols,
        },
        model_path,
    )

    now = datetime.now(timezone.utc).isoformat()
    version = f"rf-{now.replace(':', '').replace('-', '').replace('.', '')[:14]}"

    payload = {
        "model_family": "RandomForestClassifier",
        "model_version": version,
        "run_id": run_id,
        "trained_at": now,
        "config": asdict(config),
        "label_column": label_column,
        "classes_raw": [str(x) for x in le.classes_.tolist()],
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "model_selection": {
            "selected_by": "val.f1_score_weighted",
            "val_f1_score_weighted": val_metrics["f1_score"],
        },
    }

    # Include confusion matrix labeled by encoded/decoded classes.
    payload["test_label_encoding"] = {
        "encoded_classes": list(range(len(le.classes_))),
        "decoded_classes": [str(x) for x in le.classes_.tolist()],
    }

    metrics_payload = {
        "val": val_metrics,
        "test": test_metrics,
        "selected_model_version": version,
    }

    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return TrainingArtifacts(model_path=model_path, metrics_path=metrics_path, metadata_path=metadata_path)

