from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_RISK_MAP = {
    "Normal": "Low",
    "Suspect": "Medium",
    "Pathological": "Critical",
    # Fallbacks for alternative class names
    "Attack": "High",
    "Malicious": "High",
}


@dataclass(frozen=True)
class RiskResult:
    predicted_class: str
    confidence: float
    risk_level: str


def load_risk_mapping(mapping_path: Optional[Path] = None) -> Dict[str, Any]:
    if mapping_path is None:
        return dict(DEFAULT_RISK_MAP)
    p = Path(mapping_path)
    if not p.exists():
        return dict(DEFAULT_RISK_MAP)
    return json.loads(p.read_text(encoding="utf-8"))


def map_class_to_risk(predicted_class: str, risk_map: Dict[str, Any]) -> str:
    # Direct map
    if predicted_class in risk_map:
        return str(risk_map[predicted_class])

    # Common normalization
    norm = predicted_class.strip().lower()
    for k, v in risk_map.items():
        if k.strip().lower() == norm:
            return str(v)

    # Heuristic: if class looks like attack/malicious/pathological
    if "path" in norm:
        return "Critical"
    if "sus" in norm:
        return "Medium"
    if "normal" in norm:
        return "Low"
    if "mal" in norm or "attack" in norm:
        return "High"

    return "High"


def build_risk_result(predicted_class: str, confidence: float, mapping_path: Optional[Path] = None) -> RiskResult:
    risk_map = load_risk_mapping(mapping_path=mapping_path)
    risk = map_class_to_risk(predicted_class, risk_map)
    return RiskResult(predicted_class=predicted_class, confidence=float(confidence), risk_level=risk)

