import json
import sqlite3

import pytest

from aurora.config import Settings
from aurora.storage.database import Database
from aurora.storage.sessions import SQLiteSessionService


def snapshot(db):
    return db.read(lambda c: {t: [tuple(r) for r in c.execute(f"SELECT * FROM {t}")] for t in (
        "apartamentos", "areas", "reservas", "visitantes", "sessoes", "eventos", "confirmacoes", "acoes", "execucoes")})


async def test_reset_is_atomic_clears_conversations_and_preserves_sources(tmp_path):
    settings = Settings(db_path=tmp_path / "test.db")
    source = {p.name: p.read_bytes() for p in settings.data_dir.iterdir()}
    db = Database(settings)
    db.initialize()
    await SQLiteSessionService(db).create_session(app_name="aurora", user_id="101")
    db.write(lambda c: c.execute("UPDATE reservas SET status='cancelada' WHERE codigo='RSV-1377'").rowcount)
    before = snapshot(db)
    def fail(stage):
        if stage == "reset_deleted":
            raise RuntimeError("reset failed")
    db.fault = fail
    with pytest.raises(RuntimeError):
        db.reset()
    assert snapshot(db) == before
    db.fault = lambda s: None
    db.reset()
    after = snapshot(db)
    assert not after["sessoes"] and not after["eventos"] and not after["confirmacoes"]
    assert db.read(lambda c: db.reservations(c, "101"))[0]["codigo"] == "RSV-1377"
    assert source == {p.name: p.read_bytes() for p in settings.data_dir.iterdir()}


def test_partial_catalog_does_not_silently_reseed(tmp_path):
    db = Database(Settings(db_path=tmp_path / "test.db"))
    db.initialize()
    db.write(lambda c: c.execute("DELETE FROM apartamentos WHERE numero='102'").rowcount)
    before = snapshot(db)
    with pytest.raises(ValueError, match="parcialmente"):
        db.initialize()
    assert snapshot(db) == before


def test_empty_initial_import_rolls_back_on_invalid_source_reference(tmp_path):
    data = tmp_path / "dados"
    data.mkdir()
    settings = Settings(db_path=tmp_path / "test.db", data_dir=data)
    original = Settings().data_dir
    for name in ("apartamentos", "areas", "reservas", "visitantes"):
        (data / f"{name}.json").write_bytes((original / f"{name}.json").read_bytes())
    reserves = json.loads((data / "reservas.json").read_text())
    reserves[0]["apartamento"] = "999"
    (data / "reservas.json").write_text(json.dumps(reserves))
    db = Database(settings)
    with pytest.raises(sqlite3.IntegrityError):
        db.initialize()
    assert all(not rows for rows in snapshot(db).values())


def test_database_enforces_active_slot_and_never_reuses_cancelled_code(tmp_path):
    db = Database(Settings(db_path=tmp_path / "test.db"))
    db.initialize()
    with pytest.raises(sqlite3.IntegrityError):
        db.write(lambda c: c.execute("INSERT INTO reservas VALUES ('new','201','quadra','2030-03-09','ativa',NULL)").rowcount)
    db.write(lambda c: c.execute("UPDATE reservas SET status='cancelada' WHERE codigo='RSV-1377'").rowcount)
    with pytest.raises(sqlite3.IntegrityError):
        db.write(lambda c: c.execute("INSERT INTO reservas VALUES ('RSV-1377','101','quadra','2030-04-01','ativa',NULL)").rowcount)
