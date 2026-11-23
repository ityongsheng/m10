"""Optional Spark execution adapter.

The portable path uses :mod:`pipeline.local_pipeline`.  Cluster mode must be
explicitly selected and fails with a useful message when PySpark is absent;
it never silently reports a local run as a distributed run.
"""

from __future__ import annotations

from pathlib import Path
import os
from datetime import datetime, timezone

from .local_pipeline import process_rows, read_csv_bytes


def run_spark_pipeline(csv_path: str | Path, k: int = 3, contamination: float = 0.05, seed: int = 42) -> dict:
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError("cluster 模式需要安装 PySpark 3.x；当前环境未安装，未执行 Spark 任务") from exc

    builder = SparkSession.builder.appName("m10-pv-anomaly")
    master = os.getenv("SPARK_MASTER_URL")
    if master:
        builder = builder.master(master)
    spark = builder.getOrCreate()
    try:
        # Reading through Spark proves the Spark master/worker path is valid.
        frame = spark.read.option("header", True).option("inferSchema", False).csv(str(csv_path))
        spark_rows = frame.count()
        hdfs_uri = os.getenv("M10_HDFS_URI")
        hdfs_rows = None
        hdfs_path = None
        if hdfs_uri:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            hdfs_path = f"{hdfs_uri.rstrip('/')}/m10/probes/{stamp}"
            frame.write.mode("overwrite").parquet(hdfs_path)
            hdfs_rows = spark.read.parquet(hdfs_path).count()
            if hdfs_rows != spark_rows:
                raise RuntimeError(f"HDFS 回读行数不一致：写入 {spark_rows}，回读 {hdfs_rows}")
        result = process_rows(*read_csv_bytes(Path(csv_path).read_bytes())[:1], k=k, contamination=contamination, seed=seed)
        result["execution_engine"] = "spark"
        result["spark_rows"] = spark_rows
        result["hdfs_rows"] = hdfs_rows
        result["hdfs_probe_path"] = hdfs_path
        return result
    finally:
        spark.stop()

