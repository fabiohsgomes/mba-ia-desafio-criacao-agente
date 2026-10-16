"""Configuração local; credenciais nunca participam de repr/logs."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: Path = ROOT / "var/aurora.sqlite3"
    data_dir: Path = ROOT / "dados"
    model: str = "gemini-3.8-flash"
    gemini_timeout: float = 60
    busy_timeout: float = 5
    api_key: str = field(default="", repr=False)

    def __post_init__(self):
        if self.gemini_timeout <= 0 or self.busy_timeout <= 0:
            raise ValueError("Timeouts devem ser positivos")
        import math
        if not all(math.isfinite(v) for v in (self.gemini_timeout, self.busy_timeout)):
            raise ValueError("Timeouts devem ser finitos")
        if not self.model.strip():
            raise ValueError("GEMINI_MODEL vazio")

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env")
        db_path = Path(os.getenv("AURORA_DB_PATH") or "var/aurora.sqlite3")
        return cls(
            db_path=db_path if db_path.is_absolute() else ROOT / db_path,
            model=os.getenv("GEMINI_MODEL") or "gemini-3.8-flash",
            gemini_timeout=float(os.getenv("GEMINI_TIMEOUT_SECONDS") or "60"),
            busy_timeout=float(os.getenv("SQLITE_BUSY_TIMEOUT_SECONDS") or "5"),
            api_key=os.getenv("GOOGLE_API_KEY", ""),
        )
