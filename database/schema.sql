-- SQLite-compatible development schema. MySQL 8.4 deployment uses the same
-- logical tables and types through the service adapter.
CREATE TABLE IF NOT EXISTS datasets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  imported_at TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  valid_count INTEGER NOT NULL,
  invalid_count INTEGER NOT NULL,
  duplicate_count INTEGER NOT NULL DEFAULT 0,
  synthetic_demo INTEGER NOT NULL DEFAULT 0,
  source_sha256 TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS processing_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dataset_id INTEGER NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  params_json TEXT NOT NULL,
  total_rows INTEGER NOT NULL DEFAULT 0,
  anomaly_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT
);
CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  station_id TEXT NOT NULL,
  irradiance_w_m2 REAL NOT NULL,
  ambient_temp_c REAL NOT NULL,
  module_temp_c REAL NOT NULL,
  power_kw REAL NOT NULL,
  efficiency_proxy REAL NOT NULL,
  cluster_id INTEGER,
  anomaly_score REAL,
  is_anomaly INTEGER NOT NULL DEFAULT 0,
  known_issue_label INTEGER
);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  record_id INTEGER NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  acknowledged INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

