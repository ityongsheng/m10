"""Fetch and map one small, reproducible NREL PVDAQ public-data slice.

The source is downloaded from the OEDI S3 bucket linked by the U.S. Data.gov
PVDAQ catalog entry.  The mapping keeps only columns required by m10 and drops
night-time rows with negative irradiance or AC power because the current
pipeline treats those values as invalid operational records.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "real" / "raw"
OUT_DIR = ROOT / "data" / "real"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_ID = 10
DATE = "2006-07-10"
SOURCE_URL = (
    "https://oedi-data-lake.s3.amazonaws.com/pvdaq/csv/pvdata/"
    "system_id=10/year=2006/month=7/day=10/system_10__date_2006_07_10.csv"
)
SYSTEMS_URL = "https://oedi-data-lake.s3.amazonaws.com/pvdaq/csv/systems_20250729.csv"


def download(url: str, path: Path) -> bytes:
    with urlopen(url, timeout=60) as response:
        content = response.read()
    path.write_bytes(content)
    return content


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    raw_path = RAW_DIR / "system_10__date_2006_07_10.csv"
    systems_path = RAW_DIR / "systems_20250729.csv"
    raw = download(SOURCE_URL, raw_path)
    systems = download(SYSTEMS_URL, systems_path)

    metadata = next(row for row in csv.DictReader(systems.decode("utf-8-sig").splitlines()) if row["system_id"] == str(SYSTEM_ID))
    source_rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    mapped_path = OUT_DIR / "pvdaq_system10_2006-07-10.csv"
    fields = ["timestamp", "station_id", "irradiance_w_m2", "ambient_temp_c", "module_temp_c", "power_kw"]
    valid = []
    dropped = []
    for row in source_rows:
        try:
            values = {
                "timestamp": row["measured_on"],
                "station_id": f"pvdaq-{row['system_id']}",
                "irradiance_w_m2": float(row["poa_irradiance__421"]),
                "ambient_temp_c": float(row["ambient_temp__428"]),
                "module_temp_c": float(row["module_temp_1__429"]),
                "power_kw": float(row["ac_power__423"]),
            }
            if values["irradiance_w_m2"] < 0 or values["power_kw"] < 0 or values["module_temp_c"] < -90000:
                raise ValueError("negative/sentinel operational value")
        except (KeyError, TypeError, ValueError):
            dropped.append(row)
            continue
        valid.append(values)

    with mapped_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(valid)

    manifest = {
        "dataset_id": "pvdaq-system10-2006-07-10",
        "source": {
            "catalog_url": "https://catalog.data.gov/dataset/photovoltaic-data-acquisition-pvdaq-public-datasets",
            "data_url": SOURCE_URL,
            "systems_url": SYSTEMS_URL,
            "provider": "NREL / DOE PVDAQ via OEDI data lake",
            "license": "CC BY 4.0 as recorded by the Data.gov catalog entry; verify terms before redistribution",
            "retrieved_utc": "2026-11-22",
            "raw_sha256": sha256(raw),
            "systems_sha256": sha256(systems),
        },
        "system_metadata": {
            key: metadata.get(key)
            for key in ("system_id", "system_public_name", "site_location", "latitude", "longitude", "dc_capacity_kW", "qa_status")
        },
        "mapping": {
            "measured_on": "timestamp",
            "system_id": "station_id",
            "poa_irradiance__421": "irradiance_w_m2",
            "ambient_temp__428": "ambient_temp_c",
            "module_temp_1__429": "module_temp_c",
            "ac_power__423": "power_kw",
        },
        "rows": {"source": len(source_rows), "valid": len(valid), "dropped": len(dropped)},
        "mapped_sha256": sha256(mapped_path.read_bytes()),
        "mapped_path": str(mapped_path.relative_to(ROOT)),
        "synthetic": False,
        "note": "Night-time/negative-power rows were dropped to satisfy the current m10 non-negative input contract; raw source is retained for audit.",
    }
    (OUT_DIR / "pvdaq_system10_2006-07-10.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
