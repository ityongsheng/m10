from __future__ import annotations

import csv
import hashlib
import math
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Iterable, Mapping


REQUIRED_FIELDS = (
    "timestamp",
    "station_id",
    "irradiance_w_m2",
    "ambient_temp_c",
    "module_temp_c",
    "power_kw",
)
NUMERIC_FIELDS = REQUIRED_FIELDS[2:]


class PipelineInputError(ValueError):
    pass


@dataclass
class CleanStats:
    input_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    negative_rows: int = 0


def _timestamp(value: str) -> str:
    value = (value or "").strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    return parsed.isoformat()


def _float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("非有限数字")
    return number


def read_csv_bytes(content: bytes) -> tuple[list[dict], CleanStats]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PipelineInputError("CSV 必须使用 UTF-8 编码") from exc
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise PipelineInputError("CSV 缺少表头")
    missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
    if missing:
        raise PipelineInputError(f"CSV 缺少必需字段：{', '.join(missing)}")
    stats = CleanStats()
    latest: dict[tuple[str, str], dict] = {}
    for raw in reader:
        stats.input_rows += 1
        try:
            row = {
                "timestamp": _timestamp(raw.get("timestamp", "")),
                "station_id": (raw.get("station_id") or "").strip(),
                **{field: _float(raw.get(field, "")) for field in NUMERIC_FIELDS},
                "known_issue_label": (
                    int(float(raw["known_issue_label"]))
                    if raw.get("known_issue_label", "").strip() != ""
                    else None
                ),
            }
            if not row["station_id"]:
                raise ValueError("站点编号为空")
            if any(row[field] < 0 for field in ("irradiance_w_m2", "power_kw")):
                stats.negative_rows += 1
                raise ValueError("辐照度或功率不能为负")
        except (TypeError, ValueError, OverflowError):
            stats.invalid_rows += 1
            continue
        key = (row["timestamp"], row["station_id"])
        if key in latest:
            stats.duplicate_rows += 1
        latest[key] = row
    rows = list(latest.values())
    rows.sort(key=lambda row: (row["timestamp"], row["station_id"]))
    stats.valid_rows = len(rows)
    if not rows:
        raise PipelineInputError("清洗后没有可处理的有效记录")
    return rows, stats


def _features(row: Mapping) -> list[float]:
    parsed = datetime.fromisoformat(row["timestamp"])
    hour = parsed.hour + parsed.minute / 60
    angle = 2 * math.pi * hour / 24
    efficiency = row["power_kw"] / max(row["irradiance_w_m2"], 1.0)
    return [
        row["irradiance_w_m2"] / 1000.0,
        row["ambient_temp_c"] / 50.0,
        row["module_temp_c"] / 80.0,
        row["power_kw"] / 100.0,
        efficiency,
        math.sin(angle),
        math.cos(angle),
    ]


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def kmeans(features: list[list[float]], k: int, seed: int = 42) -> tuple[list[int], list[list[float]]]:
    if not features:
        return [], []
    k = max(1, min(int(k), len(features)))
    rng = random.Random(seed)
    centers = [features[i][:] for i in rng.sample(range(len(features)), k)]
    labels = [0] * len(features)
    for _ in range(40):
        changed = False
        for i, feature in enumerate(features):
            label = min(range(k), key=lambda j: _distance(feature, centers[j]))
            if label != labels[i]:
                labels[i] = label
                changed = True
        new_centers = []
        for j in range(k):
            members = [features[i] for i, label in enumerate(labels) if label == j]
            if not members:
                new_centers.append(centers[j])
            else:
                new_centers.append([sum(row[d] for row in members) / len(members) for d in range(len(features[0]))])
        centers = new_centers
        if not changed:
            break
    return labels, centers


class _IsolationTree:
    def __init__(self, rows: list[list[float]], depth: int, rng: random.Random):
        self.size = len(rows)
        self.left: _IsolationTree | None = None
        self.right: _IsolationTree | None = None
        self.split_feature: int | None = None
        self.split_value: float | None = None
        self.external = self.size <= 1 or depth <= 0
        if self.external:
            return
        candidates = [i for i in range(len(rows[0])) if max(row[i] for row in rows) > min(row[i] for row in rows)]
        if not candidates:
            self.external = True
            return
        feature = rng.choice(candidates)
        low, high = min(row[feature] for row in rows), max(row[feature] for row in rows)
        split = rng.uniform(low, high)
        left = [row for row in rows if row[feature] < split]
        right = [row for row in rows if row[feature] >= split]
        if not left or not right:
            self.external = True
            return
        self.split_feature, self.split_value = feature, split
        self.left = _IsolationTree(left, depth - 1, rng)
        self.right = _IsolationTree(right, depth - 1, rng)

    def path_length(self, row: list[float], depth: int = 0) -> float:
        if self.external:
            return depth + _average_path_length(self.size)
        assert self.split_feature is not None and self.split_value is not None
        child = self.left if row[self.split_feature] < self.split_value else self.right
        return child.path_length(row, depth + 1) if child else depth


def _average_path_length(size: int) -> float:
    if size <= 1:
        return 0.0
    if size == 2:
        return 1.0
    return 2 * (math.log(size - 1) + 0.5772156649) - 2 * (size - 1) / size


def isolation_scores(features: list[list[float]], contamination: float = 0.05, seed: int = 42) -> list[float]:
    if not features:
        return []
    rng = random.Random(seed)
    sample_size = min(64, len(features))
    depth = max(1, math.ceil(math.log2(sample_size)))
    trees = []
    for _ in range(min(80, max(20, len(features) // 2))):
        sample = rng.sample(features, sample_size)
        trees.append(_IsolationTree(sample, depth, rng))
    normalizer = max(_average_path_length(sample_size), 1.0)
    raw = [1.0 - (sum(tree.path_length(row) for tree in trees) / len(trees)) / normalizer for row in features]
    lo, hi = min(raw), max(raw)
    if hi == lo:
        return [0.0] * len(raw)
    return [(value - lo) / (hi - lo) for value in raw]


def process_rows(rows: list[dict], k: int = 3, contamination: float = 0.05, seed: int = 42) -> dict:
    feature_rows = [_features(row) for row in rows]
    labels, centers = kmeans(feature_rows, k, seed)
    scores = [0.0] * len(rows)
    for cluster in sorted(set(labels)):
        indexes = [i for i, label in enumerate(labels) if label == cluster]
        cluster_features = [feature_rows[i] for i in indexes]
        cluster_scores = isolation_scores(cluster_features, contamination, seed + cluster)
        for index, score in zip(indexes, cluster_scores):
            scores[index] = score
    threshold = sorted(scores)[max(0, math.ceil(len(scores) * (1 - contamination)) - 1)] if scores else 1.0
    for row, label, score in zip(rows, labels, scores):
        row["efficiency_proxy"] = row["power_kw"] / max(row["irradiance_w_m2"], 1.0)
        row["cluster_id"] = int(label)
        row["anomaly_score"] = round(float(score), 6)
        row["is_anomaly"] = bool(score >= threshold and score > 0)
    return {"rows": rows, "centers": centers, "threshold": threshold, "anomaly_count": sum(row["is_anomaly"] for row in rows)}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def as_public_row(row: Mapping) -> dict:
    output = dict(row)
    output["is_anomaly"] = bool(output.get("is_anomaly", False))
    return output

