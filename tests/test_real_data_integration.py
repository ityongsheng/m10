from pathlib import Path

from backend.service import import_dataset
from pipeline.local_pipeline import process_rows, read_csv_bytes


def test_pvdaq_normalized_slice_is_real_input_contract():
    root = Path(__file__).resolve().parents[1]
    path = root / "data" / "real" / "pvdaq_2107_2022-06_normalized.csv"
    content = path.read_bytes()
    result = import_dataset(path.name, content, synthetic_demo=False)
    assert result["input_rows"] == 1686
    assert result["valid_rows"] == 1686
    assert result["invalid_rows"] == 0
    assert result["duplicate_rows"] == 0

    rows, stats = read_csv_bytes(content)
    processed = process_rows(rows, k=3, contamination=0.05)
    assert stats.valid_rows == 1686
    assert len({row["cluster_id"] for row in processed["rows"]}) == 3
    assert processed["anomaly_count"] > 0
