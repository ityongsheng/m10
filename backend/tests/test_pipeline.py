from pathlib import Path

import pytest

from pipeline.local_pipeline import PipelineInputError, process_rows, read_csv_bytes


SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample" / "pv_demo.csv"


def test_demo_csv_is_cleaned_and_processed():
    rows, stats = read_csv_bytes(SAMPLE.read_bytes())
    assert stats.input_rows == stats.valid_rows == 576
    result = process_rows(rows, k=3, contamination=0.05)
    assert len(result["rows"]) == stats.valid_rows
    assert all("cluster_id" in row for row in result["rows"])
    assert any(row["is_anomaly"] for row in result["rows"])


def test_missing_required_field_is_rejected():
    with pytest.raises(PipelineInputError, match="缺少必需字段"):
        read_csv_bytes(b"timestamp,station_id,power_kw\n2026-01-01T00:00:00Z,A,1\n")


def test_duplicate_keeps_latest_and_negative_is_invalid():
    content = b"timestamp,station_id,irradiance_w_m2,ambient_temp_c,module_temp_c,power_kw\n2026-01-01T00:00:00Z,A,100,20,25,1\n2026-01-01T00:00:00Z,A,200,20,25,2\n2026-01-01T00:30:00Z,A,-1,20,25,2\n"
    rows, stats = read_csv_bytes(content)
    assert len(rows) == 1
    assert stats.duplicate_rows == 1
    assert stats.negative_rows == 1

