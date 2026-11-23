"""Normalize a small, reproducible PVDAQ public-data slice for m10.

The source system publishes irradiance, ambient temperature and AC meter
channels separately.  This script joins them on the source timestamp and
converts Fahrenheit to Celsius.  PVDAQ system 2107 does not publish a module
temperature channel in the selected files, so module_temp_c is explicitly an
ambient-temperature proxy and is recorded as such in the dataset README.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "data" / "real"


def build(start: str, end: str, output: Path) -> dict[str, object]:
    meter = pd.read_csv(REAL / "pvdaq_2107_meter_15m_data.csv")
    env = pd.read_csv(REAL / "pvdaq_2107_environment_data.csv")
    irr = pd.read_csv(REAL / "pvdaq_2107_irradiance_data.csv")

    meter["timestamp"] = pd.to_datetime(meter.pop("measured_on"), errors="coerce")
    env["timestamp"] = pd.to_datetime(env.pop("measured_on"), errors="coerce")
    irr["timestamp"] = pd.to_datetime(irr.pop("measured_on"), errors="coerce")

    meter = meter.rename(columns={meter.columns[0]: "power_kw"})
    env = env.rename(columns={env.columns[0]: "ambient_f"})
    irr = irr.rename(columns={irr.columns[0]: "irradiance_w_m2"})
    joined = meter.merge(env, on="timestamp", how="inner").merge(irr, on="timestamp", how="inner")
    joined = joined[(joined["timestamp"] >= pd.Timestamp(start)) & (joined["timestamp"] < pd.Timestamp(end))]
    joined["ambient_temp_c"] = (pd.to_numeric(joined["ambient_f"], errors="coerce") - 32.0) * 5.0 / 9.0
    # System 2107 has no module-temperature metric in the selected PVDAQ
    # metadata. Keep the required project field while exposing the proxy in
    # data/real/README.md and the manifest.
    joined["module_temp_c"] = joined["ambient_temp_c"]
    joined["station_id"] = "PVDAQ-2107"
    out = joined[["timestamp", "station_id", "irradiance_w_m2", "ambient_temp_c", "module_temp_c", "power_kw"]]
    out = out.dropna().sort_values("timestamp").drop_duplicates(["timestamp", "station_id"])
    out.to_csv(output, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    return {
        "source_system": 2107,
        "source_period": {"start_inclusive": start, "end_exclusive": end},
        "rows": int(len(out)),
        "timestamp_min": out["timestamp"].min().isoformat() if len(out) else None,
        "timestamp_max": out["timestamp"].max().isoformat() if len(out) else None,
        "ambient_conversion": "Fahrenheit to Celsius",
        "module_temp_mapping": "ambient_temp_c proxy; source channel not published",
        "output": str(output.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2022-06-01")
    parser.add_argument("--end", default="2022-07-01")
    parser.add_argument("--output", default="data/real/pvdaq_2107_2022-06_normalized.csv")
    args = parser.parse_args()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    print(build(args.start, args.end, output))


if __name__ == "__main__":
    main()
