import os
import subprocess
import sys

from aurora.config import ROOT, Settings
from aurora.storage.database import Database


def test_reset_command_restores_seed_and_does_not_require_api_key(tmp_path):
    settings = Settings(db_path=tmp_path / "cli.db")
    db = Database(settings)
    db.initialize()
    db.write(lambda c: c.execute("UPDATE reservas SET status='cancelada' WHERE codigo='RSV-1377'").rowcount)
    env = {**os.environ, "AURORA_DB_PATH": str(settings.db_path), "GOOGLE_API_KEY": "",
           "GEMINI_MODEL": "", "GEMINI_TIMEOUT_SECONDS": "", "SQLITE_BUSY_TIMEOUT_SECONDS": ""}
    result = subprocess.run([sys.executable, "-m", "aurora", "reset"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0
    assert "Dados restaurados" in result.stdout
    assert db.read(lambda c: db.reservations(c, "101"))[0]["codigo"] == "RSV-1377"


def test_invalid_timeout_configuration_fails_without_disclosing_values(tmp_path):
    env = {**os.environ, "AURORA_DB_PATH": str(tmp_path / "bad.db"), "GEMINI_TIMEOUT_SECONDS": "invalid-sensitive-value"}
    result = subprocess.run([sys.executable, "-m", "aurora", "reset"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert "ValueError" in result.stdout
    assert "invalid-sensitive-value" not in result.stdout + result.stderr
