from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.db import connection, init_db, json_text, now_iso
from pipeline.local_pipeline import (
    PipelineInputError,
    as_public_row,
    process_rows,
    read_csv_bytes,
    sha256_bytes,
)
from pipeline.spark_pipeline import run_spark_pipeline


class ServiceError(RuntimeError):
    pass


def ensure_ready() -> None:
    settings.ensure_dirs()
    init_db()


def import_dataset(filename: str, content: bytes, synthetic_demo: bool = False) -> dict:
    if len(content) > settings.max_upload_bytes:
        raise ServiceError("上传文件超过 25 MB 限制")
    rows, stats = read_csv_bytes(content)
    source_hash = sha256_bytes(content)
    ensure_ready()
    with connection() as conn:
        cursor = conn.execute(
            """INSERT INTO datasets(filename, imported_at, row_count, valid_count, invalid_count,
               duplicate_count, synthetic_demo, source_sha256, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                filename,
                now_iso(),
                stats.input_rows,
                stats.valid_rows,
                stats.invalid_rows,
                stats.duplicate_rows,
                int(synthetic_demo),
                source_hash,
                json_text({"negative_rows": stats.negative_rows}),
            ),
        )
        dataset_id = cursor.lastrowid
    return {"id": dataset_id, "filename": filename, "sha256": source_hash, **stats.__dict__}


def list_datasets() -> list[dict]:
    ensure_ready()
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM datasets ORDER BY id DESC")]


def _dataset_content(dataset_id: int) -> bytes:
    # Imported datasets are kept as source files under runtime/uploads.
    path = settings.data_root / "uploads" / f"dataset-{dataset_id}.csv"
    if not path.exists():
        raise ServiceError("找不到数据源文件，请重新导入")
    return path.read_bytes()


def save_dataset_source(dataset_id: int, content: bytes) -> None:
    path = settings.data_root / "uploads" / f"dataset-{dataset_id}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def run_dataset(dataset_id: int, k: int = 3, contamination: float = 0.05, mode: str | None = None) -> dict:
    ensure_ready()
    mode = mode or settings.mode
    content = _dataset_content(dataset_id)
    started = now_iso()
    with connection() as conn:
        dataset = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
        if dataset is None:
            raise ServiceError("数据集不存在")
        cursor = conn.execute(
            "INSERT INTO processing_runs(dataset_id, mode, status, started_at, params_json) VALUES (?, ?, ?, ?, ?)",
            (dataset_id, mode, "running", started, json_text({"k": k, "contamination": contamination, "seed": 42})),
        )
        run_id = cursor.lastrowid
    try:
        if mode == "cluster":
            source_path = settings.data_root / "uploads" / f"dataset-{dataset_id}.csv"
            result = run_spark_pipeline(source_path, k=k, contamination=contamination)
            rows, stats = read_csv_bytes(content)
        else:
            rows, stats = read_csv_bytes(content)
            result = process_rows(rows, k=k, contamination=contamination)
        with connection() as conn:
            for row in result["rows"]:
                cursor = conn.execute(
                    """INSERT INTO records(run_id, timestamp, station_id, irradiance_w_m2, ambient_temp_c,
                       module_temp_c, power_kw, efficiency_proxy, cluster_id, anomaly_score, is_anomaly,
                       known_issue_label) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        row["timestamp"], row["station_id"], row["irradiance_w_m2"], row["ambient_temp_c"],
                        row["module_temp_c"], row["power_kw"], row["efficiency_proxy"], row["cluster_id"],
                        row["anomaly_score"], int(row["is_anomaly"]), row.get("known_issue_label"),
                    ),
                )
                if row["is_anomaly"]:
                    record_id = cursor.lastrowid
                    severity = "high" if row["anomaly_score"] >= 0.85 else "medium"
                    conn.execute(
                        "INSERT INTO alerts(run_id, record_id, severity, message, created_at) VALUES (?, ?, ?, ?, ?)",
                        (run_id, record_id, severity, f"站点 {row['station_id']} 在 {row['timestamp']} 检测到发电效率异常", now_iso()),
                    )
            conn.execute(
                "UPDATE processing_runs SET status=?, completed_at=?, total_rows=?, anomaly_count=? WHERE id=?",
                ("completed", now_iso(), len(result["rows"]), result["anomaly_count"], run_id),
            )
        return {
            "id": run_id,
            "status": "completed",
            "total_rows": len(result["rows"]),
            "anomaly_count": result["anomaly_count"],
            "threshold": result["threshold"],
            "clean_stats": stats.__dict__,
            "execution_engine": result.get("execution_engine", "local"),
            "spark_rows": result.get("spark_rows"),
            "hdfs_rows": result.get("hdfs_rows"),
            "hdfs_probe_path": result.get("hdfs_probe_path"),
        }
    except Exception as exc:
        with connection() as conn:
            conn.execute("UPDATE processing_runs SET status=?, completed_at=?, error_message=? WHERE id=?", ("failed", now_iso(), str(exc), run_id))
        if isinstance(exc, PipelineInputError):
            raise
        raise ServiceError(str(exc)) from exc


def list_runs() -> list[dict]:
    ensure_ready()
    with connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM processing_runs ORDER BY id DESC")]


def overview(run_id: int) -> dict:
    ensure_ready()
    with connection() as conn:
        run = conn.execute("SELECT * FROM processing_runs WHERE id=?", (run_id,)).fetchone()
        if run is None:
            raise ServiceError("运行记录不存在")
        stats = conn.execute(
            "SELECT COUNT(*) total, SUM(is_anomaly) anomalies, AVG(power_kw) avg_power, AVG(efficiency_proxy) avg_efficiency FROM records WHERE run_id=?",
            (run_id,),
        ).fetchone()
        clusters = [dict(row) for row in conn.execute("SELECT cluster_id, COUNT(*) count FROM records WHERE run_id=? GROUP BY cluster_id ORDER BY cluster_id", (run_id,))]
        return {"run": dict(run), "metrics": dict(stats), "clusters": clusters}


def records(run_id: int, anomalies_only: bool = False, station_id: str | None = None, limit: int = 500) -> list[dict]:
    ensure_ready()
    limit = max(1, min(int(limit), 5000))
    sql = "SELECT * FROM records WHERE run_id=?"
    params: list[Any] = [run_id]
    if anomalies_only:
        sql += " AND is_anomaly=1"
    if station_id:
        sql += " AND station_id=?"
        params.append(station_id)
    sql += " ORDER BY timestamp, station_id LIMIT ?"
    params.append(limit)
    with connection() as conn:
        output = []
        for row in conn.execute(sql, params):
            payload = as_public_row(dict(row))
            score = float(payload.get("anomaly_score") or 0)
            payload["severity"] = "high" if score >= 0.85 else ("medium" if payload.get("is_anomaly") else "low")
            output.append(payload)
        return output


def alerts(run_id: int | None = None) -> list[dict]:
    ensure_ready()
    sql = "SELECT * FROM alerts"
    params: list[Any] = []
    if run_id is not None:
        sql += " WHERE run_id=?"
        params.append(run_id)
    sql += " ORDER BY id DESC"
    with connection() as conn:
        return [dict(row) for row in conn.execute(sql, params)]

