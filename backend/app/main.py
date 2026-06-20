from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.routers.dashboard import router as dashboard_router
from app.routers.health import router as health_router
from app.routers.model import router as model_router

app = FastAPI(title="AI-Enhanced IDS Backend", version="0.1.0")

app.include_router(health_router)
app.include_router(model_router)
app.include_router(dashboard_router)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    dashboard_path = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard file not found")
    return HTMLResponse(dashboard_path.read_text(encoding="utf-8"))


@app.get("/")
def root():
    return {
        "title": "AI-Enhanced Intrusion Detection System Backend",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "dashboard_overview": "GET /api/dashboard/overview",
            "alerts_latest": "GET /api/alerts/latest",
            "reports_summary": "GET /api/reports/summary",
            "model_train": "POST /api/model/train",
            "model_current": "GET /api/model/current",
            "inference_predict": "POST /api/inference/predict",
            "api_docs": "GET /docs",
            "openapi_schema": "GET /openapi.json",
        },
    }



