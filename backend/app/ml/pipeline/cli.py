from __future__ import annotations

import argparse
from pathlib import Path

from app.ml.pipeline.config import PipelineConfig
from app.ml.pipeline.run_pipeline import run_phase2_pipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 2: Data pipeline & feature engineering")

    p.add_argument("--dataset-name", default="dataset", help="Logical dataset name")
    p.add_argument("--run-id", default=None, help="Optional run identifier")

    p.add_argument("--input-file", required=True, help="Path to input CSV file")
    p.add_argument(
        "--output-dir",
        default=str(Path("backend/data/processed").resolve()),
        help="Base output directory",
    )

    p.add_argument("--label-column", required=True, help="Name of label/target column")
    p.add_argument(
        "--categorical-columns",
        default="",
        help="Comma-separated list of categorical columns (optional)",
    )
    p.add_argument(
        "--numerical-columns",
        default="",
        help="Comma-separated list of numerical columns (optional)",
    )
    p.add_argument(
        "--ignore-columns",
        default="",
        help="Comma-separated list of columns to ignore (optional)",
    )

    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--val-size", type=float, default=0.1)
    p.add_argument("--random-state", type=int, default=42)

    p.add_argument("--no-drop-duplicates", action="store_true", help="Disable duplicate removal")
    p.add_argument(
        "--fill-missing-strategy",
        default="median",
        choices=["median", "mean", "zero"],
        help="Missing-value strategy for numerical columns",
    )
    p.add_argument(
        "--categorical-missing-strategy",
        default="__MISSING__",
        help="Missing-value token for categorical columns",
    )

    p.add_argument("--enable-feature-selection", action="store_true")
    p.add_argument("--feature-selection-k", type=int, default=50)

    return p.parse_args()


def main() -> None:
    args = parse_args()

    def split_csv(s: str) -> list[str]:
        s = (s or "").strip()
        if not s:
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    cfg = PipelineConfig(
        input_file=Path(args.input_file),
        output_dir=Path(args.output_dir),
        dataset_name=args.dataset_name,
        run_id=args.run_id,
        label_column=args.label_column,
        categorical_columns=split_csv(args.categorical_columns),
        numerical_columns=split_csv(args.numerical_columns),
        ignore_columns=split_csv(args.ignore_columns),
        test_size=args.test_size,
        val_size=args.val_size,
        random_state=args.random_state,
        drop_duplicates=not args.no_drop_duplicates,
        fill_missing_strategy=args.fill_missing_strategy,
        categorical_missing_strategy=args.categorical_missing_strategy,
        enable_feature_selection=args.enable_feature_selection,
        feature_selection_k=args.feature_selection_k,
    )

    metadata = run_phase2_pipeline(cfg)
    # Print a short summary for CLI usage
    print("Phase 2 completed.")
    print(f"Rows total: {metadata['dataset_statistics']['rows_total']}")
    print(f"Encoded features: {metadata['dataset_statistics']['features_encoded']}")


if __name__ == "__main__":
    main()

