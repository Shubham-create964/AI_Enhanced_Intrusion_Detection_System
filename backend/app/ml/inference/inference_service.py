from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import joblib
import numpy as np

from app.ml.inference.risk import RiskResult, build_risk_result


@dataclass(frozen=True)
class InferenceArtifacts:
    preprocessor_path: Path
    model_path: Path


class InferenceService:
    def __init__(
        self,
        *,
        preprocessor: Any,
        model_bundle: Dict[str, Any],
        risk_mapping_path: Optional[Path] = None,
    ) -> None:
        self.preprocessor = preprocessor
        self.model = model_bundle["model"]
        self.label_encoder = model_bundle["label_encoder"]
        self.feature_columns: List[str] = model_bundle["feature_columns"]
        self.risk_mapping_path = risk_mapping_path

    @staticmethod
    def load(*, preprocessor_path: Path, model_path: Path, risk_mapping_path: Optional[Path] = None) -> "InferenceService":
        preprocessor = joblib.load(preprocessor_path)
        bundle = joblib.load(model_path)
        return InferenceService(preprocessor=preprocessor, model_bundle=bundle, risk_mapping_path=risk_mapping_path)

    def predict_from_dataframe(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # rows are raw feature dicts in original dataset schema.
        import pandas as pd

        df = pd.DataFrame(rows)

        # Preprocessor artifacts include the fitted transformer and any selector.
        if hasattr(self.preprocessor, "transformer"):
            X = self.preprocessor.transformer.transform(df)
        else:
            X = self.preprocessor.transform(df)

        if hasattr(self.preprocessor, "selector") and self.preprocessor.selector is not None:
            X = self.preprocessor.selector.transform(X)

        y_pred_enc = self.model.predict(X)
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
        out: List[Dict[str, Any]] = []

        for i, pred_enc in enumerate(y_pred_enc):
            predicted_class_raw = str(self.label_encoder.inverse_transform([pred_enc])[0])
            confidence = float(np.max(proba[i])) if proba is not None else 0.0
            risk: RiskResult = build_risk_result(
                predicted_class=predicted_class_raw,
                confidence=confidence,
                mapping_path=self.risk_mapping_path,
            )
            out.append(
                {
                    "predicted_class": predicted_class_raw,
                    "confidence": confidence,
                    "risk_level": risk.risk_level,
                }
            )
        return out

    def predict_from_vector(self, vector: Sequence[float]) -> Dict[str, Any]:
        X = np.asarray(vector, dtype=float).reshape(1, -1)
        y_pred_enc = self.model.predict(X)
        pred_enc = int(y_pred_enc[0])
        predicted_class_raw = str(self.label_encoder.inverse_transform([pred_enc])[0])
        confidence = 0.0
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
            confidence = float(np.max(proba[0]))
        risk = build_risk_result(predicted_class=predicted_class_raw, confidence=confidence, mapping_path=self.risk_mapping_path)
        return {"predicted_class": predicted_class_raw, "confidence": confidence, "risk_level": risk.risk_level}

