from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.service import (
    PipelineInputError,
    ServiceError,
    alerts,
    ensure_ready,
    import_dataset,
    list_datasets,
    list_runs,
    overview,
    records,
    run_dataset,
    save_dataset_source,
)
from backend.config import PROJECT_ROOT, settings


app = FastAPI(title="光伏电站发电效率异常检测系统", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
_frontend_dir = PROJECT_ROOT / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")
_data_dir = PROJECT_ROOT / "data"
if _data_dir.exists():
    app.mount("/data", StaticFiles(directory=_data_dir), name="data")


class RunRequest(BaseModel):
    dataset_id: int | None = Field(default=None, gt=0)
    k: int = Field(default=3, ge=2, le=8)
    contamination: float = Field(default=0.05, gt=0, lt=0.5)
    mode: str = Field(default="local", pattern="^(local|cluster)$")
    use_demo: bool = False
    use_real: bool = False
    note: str | None = Field(default=None, max_length=80)


@app.on_event("startup")
def startup() -> None:
    ensure_ready()


@app.get("/api/health")
def health() -> dict[str, Any]:
    ensure_ready()
    return {"status": "ok", "service": "m10", "mode": settings.mode}


@app.post("/api/datasets/import")
async def import_csv(file: UploadFile = File(...), synthetic_demo: bool = Query(False)) -> dict:
    content = await file.read()
    try:
        result = import_dataset(file.filename or "upload.csv", content, synthetic_demo)
        save_dataset_source(result["id"], content)
        return result
    except (PipelineInputError, ServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/datasets")
def datasets() -> list[dict]:
    return list_datasets()


@app.post("/api/runs")
def create_run(request: RunRequest) -> dict:
    try:
        dataset_id = request.dataset_id
        if dataset_id is None and request.use_demo:
            demo_path = PROJECT_ROOT / "data" / "sample" / "pv_demo.csv"
            if not demo_path.exists():
                raise ServiceError("项目演示数据不存在")
            imported = import_dataset(demo_path.name, demo_path.read_bytes(), synthetic_demo=True)
            save_dataset_source(imported["id"], demo_path.read_bytes())
            dataset_id = imported["id"]
        if dataset_id is None and request.use_real:
            real_path = PROJECT_ROOT / "data" / "real" / "pvdaq_2107_2022-06_normalized.csv"
            if not real_path.exists():
                raise ServiceError("项目内 PVDAQ 真实数据切片不存在")
            content = real_path.read_bytes()
            imported = import_dataset(real_path.name, content, synthetic_demo=False)
            save_dataset_source(imported["id"], content)
            dataset_id = imported["id"]
        if dataset_id is None:
            raise ServiceError("必须提供 dataset_id，或选择项目演示数据/真实 PVDAQ 数据")
        return run_dataset(dataset_id, request.k, request.contamination, request.mode)
    except (PipelineInputError, ServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/runs")
def runs() -> list[dict]:
    return list_runs()


@app.get("/api/runs/{run_id}/overview")
def run_overview(run_id: int) -> dict:
    try:
        return overview(run_id)
    except ServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/metrics/overview")
def latest_overview() -> dict:
    """Return the most recent completed run in the shape used by the dashboard."""
    latest = list_runs()
    completed = next((item for item in latest if item.get("status") == "completed"), None)
    if completed is None:
        return {"record_count": 0, "anomaly_count": 0, "alert_count": 0, "cluster_count": 0}
    result = overview(int(completed["id"]))
    metrics = result.get("metrics", {})
    return {
        "run_id": completed["id"],
        "record_count": metrics.get("total") or 0,
        "anomaly_count": metrics.get("anomalies") or 0,
        "alert_count": len(alerts(int(completed["id"]))),
        "cluster_count": len(result.get("clusters", [])),
    }


@app.get("/api/timeseries")
def latest_timeseries(limit: int = Query(5000, ge=1, le=5000)) -> list[dict]:
    latest = next((item for item in list_runs() if item.get("status") == "completed"), None)
    return records(int(latest["id"]), limit=limit) if latest else []


@app.get("/api/anomalies")
def latest_anomalies(limit: int = Query(5000, ge=1, le=5000)) -> list[dict]:
    latest = next((item for item in list_runs() if item.get("status") == "completed"), None)
    return records(int(latest["id"]), anomalies_only=True, limit=limit) if latest else []


@app.get("/api/runs/{run_id}/records")
def run_records(run_id: int, anomalies_only: bool = False, station_id: str | None = None, limit: int = Query(500, ge=1, le=5000)) -> list[dict]:
    return records(run_id, anomalies_only, station_id, limit)


@app.get("/api/runs/{run_id}/alerts")
def run_alerts(run_id: int) -> list[dict]:
    return alerts(run_id)


@app.get("/api/alerts")
def all_alerts() -> list[dict]:
    return alerts()


@app.get("/")
def index() -> FileResponse:
    frontend = PROJECT_ROOT / "frontend" / "index.html"
    if not frontend.exists():
        raise HTTPException(status_code=404, detail="前端文件尚未构建")
    return FileResponse(frontend)

