from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class PipelineConfig:
    # Input/output
    input_file: Path
    output_dir: Path

    # Dataset schema override
    label_column: str
    categorical_columns: List[str] = field(default_factory=list)
    numerical_columns: List[str] = field(default_factory=list)
    ignore_columns: List[str] = field(default_factory=list)

    # Split params
    test_size: float = 0.2
    val_size: float = 0.1  # relative to full dataset
    random_state: int = 42

    # Feature engineering
    drop_duplicates: bool = True
    fill_missing_strategy: str = "median"  # numerical: median/mean/zero
    categorical_missing_strategy: str = "__MISSING__"

    # Feature selection
    # If True, performs SelectKBest(chi2) on categorical+numerical encoded features.
    # Note: chi2 requires non-negative; we use StandardScaler -> shifts may break.
    # For robustness we default to no feature selection here unless explicitly enabled.
    enable_feature_selection: bool = False
    feature_selection_k: int = 50

    # Processing metadata
    dataset_name: str = "dataset"
    run_id: Optional[str] = None

    # Output format
    parquet_engine: str = "pyarrow"  # kept for future; currently pandas will pick available engine.


def build_output_paths(cfg: PipelineConfig) -> dict[str, Path]:
    """Creates and returns a deterministic folder structure for this run."""

    run_id = cfg.run_id or "run"
    base = cfg.output_dir / cfg.dataset_name / run_id
    return {
        "base": base,
        "splits": base / "splits",
        "artifacts": base / "artifacts",
        "reports": base / "reports",
        "metadata": base / "metadata.json",
        "preprocess_report": base / "reports" / "preprocessing_report.json",
        "dataset_report": base / "reports" / "dataset_statistics.json",
        "features_schema": base / "artifacts" / "features_schema.json",
        "feature_mappings": base / "artifacts" / "feature_mappings.json",
        "preprocessors": base / "artifacts" / "preprocessors.joblib",
    }

