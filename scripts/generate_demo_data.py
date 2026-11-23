"""Generate deterministic synthetic PV data for development only."""
from __future__ import annotations
import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20261122
OUT = Path(__file__).resolve().parents[1] / "data" / "sample" / "pv_demo.csv"


def main() -> None:
    rng = random.Random(SEED)
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    stations = [("PV-A", 45.0), ("PV-B", 52.0)]
    rows = []
    for i in range(288):
        ts = start + timedelta(minutes=30 * i)
        hour = ts.hour + ts.minute / 60
        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        for station_id, capacity in stations:
            irradiance = max(0.0, 980 * daylight + rng.gauss(0, 18))
            ambient = 19 + 7 * daylight + rng.gauss(0, 1.2)
            module = ambient + 0.028 * irradiance + rng.gauss(0, 0.8)
            power = max(0.0, capacity * (irradiance / 1000) * (1 - 0.002 * (module - 25)) + rng.gauss(0, 0.7))
            label = 0
            if station_id == "PV-B" and i in {74, 75, 76, 185, 186}:
                power *= 0.38
                label = 1
            if station_id == "PV-A" and i in {121, 122}:
                module += 18
                power *= 0.58
                label = 1
            rows.append({
                "timestamp": ts.isoformat().replace("+00:00", "Z"),
                "station_id": station_id,
                "irradiance_w_m2": round(irradiance, 3),
                "ambient_temp_c": round(ambient, 3),
                "module_temp_c": round(module, 3),
                "power_kw": round(power, 3),
                "known_issue_label": label,
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
