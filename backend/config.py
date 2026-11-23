from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("M10_RUNTIME_MODE", "local")
    database_url: str = os.getenv(
        "M10_DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'runtime' / 'm10.sqlite3'}"
    )
    data_root: Path = Path(os.getenv("M10_DATA_ROOT", str(PROJECT_ROOT / "runtime")))
    max_upload_bytes: int = int(os.getenv("M10_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))

    def ensure_dirs(self) -> None:
        self.data_root.mkdir(parents=True, exist_ok=True)


settings = Settings()

