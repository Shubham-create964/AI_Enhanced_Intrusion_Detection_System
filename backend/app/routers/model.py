from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.inference.inference_service import InferenceService
from app.ml.training.train_rf import RFTrainingConfig, train_random_forest


router = APIRouter(tags=["model"])


class TrainRequest(BaseModel):
    # Use Phase-2 outputs already on disk.
    # label_column must match the Phase-2 split parquet label column.
    label_column: str = Field(..., description="Target/label column name used during Phase 2")

    dataset_name: str = Field(default="dataset")
    run_id: Optional[str] = Field(default=None, description="Existing run_id folder or new one")

    # Phase-2 base output dir where preprocessors.joblib and splits/*.parquet exist.
    phase2_output_dir: str = Field(default=str(Path("backend/data/processed").resolve()))

    # Model hyperparameters
    n_estimators: int = 300
    max_depth: Optional[int] = None


class InferencePredictRequest(BaseModel):
    # Raw feature rows in original schema.
    # Example: {"f1": 1.2, "protocol": "tcp", ...}
    rows: list[dict[str, Any]]


class TrainResponse(BaseModel):
    run_id: str
    model_version: str
    metrics: Dict[str, Any]


MODEL_CURRENT_PATH = Path("backend/models/current.json")


def _current_model_paths(*, base_dir: Path, dataset_name: str, run_id: str) -> dict[str, Path]:
    run_dir = base_dir / dataset_name / run_id
    return {
        "preprocessor": run_dir / "artifacts" / "preprocessors.joblib",
        "train": run_dir / "splits" / "train.parquet",
        "val": run_dir / "splits" / "val.parquet",
        "test": run_dir / "splits" / "test.parquet",
        "model_dir": run_dir / "artifacts" / "model",
    }


def _ensure_current_json() -> None:
    MODEL_CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MODEL_CURRENT_PATH.exists():
        MODEL_CURRENT_PATH.write_text(json.dumps({}, indent=2), encoding="utf-8")


@router.post("/api/model/train", response_model=TrainResponse)
def train_model(req: TrainRequest) -> TrainResponse:
    base_dir = Path(req.phase2_output_dir)
    run_id = req.run_id or str(uuid.uuid4())

    paths = _current_model_paths(base_dir=base_dir, dataset_name=req.dataset_name, run_id=run_id)
    for p in [paths["preprocessor"], paths["train"], paths["val"], paths["test"]]:
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"Required Phase2 artifact missing: {p}")

    paths["model_dir"].mkdir(parents=True, exist_ok=True)

    artifacts = train_random_forest(
        train_path=paths["train"],
        val_path=paths["val"],
        test_path=paths["test"],
        label_column=req.label_column,
        out_dir=paths["model_dir"],
        config=RFTrainingConfig(n_estimators=req.n_estimators, max_depth=req.max_depth),
        run_id=run_id,
    )

    metadata = json.loads(artifacts.metadata_path.read_text(encoding="utf-8"))
    metrics = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))

    # Update current pointer
    _ensure_current_json()
    current_payload = {
        "dataset_name": req.dataset_name,
        "run_id": run_id,
        "model_version": metadata.get("model_version"),
        "model_path": str(artifacts.model_path),
        "preprocessor_path": str(paths["preprocessor"]),
        "trained_at": metadata.get("trained_at"),
    }
    MODEL_CURRENT_PATH.write_text(json.dumps(current_payload, indent=2), encoding="utf-8")

    return TrainResponse(run_id=run_id, model_version=current_payload["model_version"], metrics=metrics)


@router.get("/api/model/current")
def get_current_model() -> Dict[str, Any]:
    _ensure_current_json()
    if not MODEL_CURRENT_PATH.exists():
        raise HTTPException(status_code=404, detail="No current model registered")
    data = json.loads(MODEL_CURRENT_PATH.read_text(encoding="utf-8"))
    if not data:
        raise HTTPException(status_code=404, detail="No current model registered")
    return data


@router.post("/api/inference/predict")
def predict(req: InferencePredictRequest) -> Dict[str, Any]:
    if not MODEL_CURRENT_PATH.exists():
        raise HTTPException(status_code=404, detail="No trained model available. Train first.")

    current = json.loads(MODEL_CURRENT_PATH.read_text(encoding="utf-8"))
    if not current:
        raise HTTPException(status_code=404, detail="No trained model available. Train first.")

    preprocessor_path = Path(current["preprocessor_path"])
    model_path = Path(current["model_path"])

    if not preprocessor_path.exists() or not model_path.exists():
        raise HTTPException(status_code=500, detail="Model artifacts referenced by current.json are missing")

    # Optional risk mapping
    risk_map_path = Path(os.environ.get("RISK_MAPPING_PATH", "")) if os.environ.get("RISK_MAPPING_PATH") else None

    svc = InferenceService.load(preprocessor_path=preprocessor_path, model_path=model_path, risk_mapping_path=risk_map_path)

    preds = svc.predict_from_dataframe(req.rows)
    return {"predictions": preds, "model_version": current.get("model_version")}

