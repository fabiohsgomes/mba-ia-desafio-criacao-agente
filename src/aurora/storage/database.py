"""Única fronteira SQL e transacional: conexão e callback vivem no mesmo thread."""
import asyncio
import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Callable, TypeVar

from aurora.config import Settings

T = TypeVar("T")
SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS apartamentos (numero TEXT PRIMARY KEY, morador TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS areas (id TEXT PRIMARY KEY, nome TEXT NOT NULL, taxa_centavos INTEGER NOT NULL CHECK(taxa_centavos>=0));
CREATE TABLE IF NOT EXISTS reservas (
 codigo TEXT PRIMARY KEY, apartamento TEXT NOT NULL REFERENCES apartamentos(numero),
 area TEXT NOT NULL REFERENCES areas(id), data TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('ativa','cancelada')), acao_id TEXT UNIQUE);
CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_ativa ON reservas(area,data) WHERE status='ativa';
CREATE TABLE IF NOT EXISTS visitantes (
 id TEXT PRIMARY KEY, apartamento TEXT NOT NULL REFERENCES apartamentos(numero),
 nome TEXT NOT NULL, data TEXT NOT NULL, acao_id TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS sessoes (
 id TEXT PRIMARY KEY, app_name TEXT NOT NULL, apartamento TEXT NOT NULL REFERENCES apartamentos(numero),
 estado TEXT NOT NULL, versao INTEGER NOT NULL DEFAULT 0, atualizado REAL NOT NULL);
CREATE TRIGGER IF NOT EXISTS apartamento_imutavel BEFORE UPDATE OF apartamento ON sessoes
 WHEN OLD.apartamento != NEW.apartamento BEGIN SELECT RAISE(ABORT, 'apartamento imutavel'); END;
CREATE TABLE IF NOT EXISTS eventos (
 session_id TEXT NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
 sequencia INTEGER NOT NULL, id TEXT NOT NULL, invocation_id TEXT NOT NULL,
 autor TEXT NOT NULL, evento TEXT NOT NULL, PRIMARY KEY(session_id,sequencia), UNIQUE(session_id,id));
CREATE TABLE IF NOT EXISTS confirmacoes (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
 invocation_id TEXT NOT NULL, autor TEXT NOT NULL, tool_call_id TEXT NOT NULL,
 acao TEXT NOT NULL, argumentos TEXT NOT NULL, detalhes TEXT NOT NULL,
 estado TEXT NOT NULL DEFAULT 'pendente', resposta INTEGER, resultado TEXT);
CREATE TABLE IF NOT EXISTS execucoes (
 session_id TEXT NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
 invocation_id TEXT NOT NULL, autor TEXT NOT NULL, checkpoint TEXT NOT NULL,
 PRIMARY KEY(session_id,invocation_id));
CREATE TABLE IF NOT EXISTS acoes (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
 invocation_id TEXT NOT NULL, tool_call_id TEXT NOT NULL, resultado TEXT NOT NULL,
 UNIQUE(session_id,invocation_id,tool_call_id));
"""


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        # Test-only fault injection: called within the transaction, never logs data.
        self.fault: Callable[[str], None] = lambda stage: None

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.settings.db_path, timeout=self.settings.busy_timeout, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        try:
            yield conn
        finally:
            conn.close()

    def read(self, callback: Callable[[sqlite3.Connection], T]) -> T:
        with self.connection() as conn:
            return callback(conn)

    def write(self, callback: Callable[[sqlite3.Connection], T]) -> T:
        from aurora.observability import emit
        start = time.monotonic()
        outcome = "rollback"
        try:
            with self.connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    result = callback(conn)
                    self.fault("before_commit")
                    conn.execute("COMMIT")
                    outcome = "commit"
                    return result
                except BaseException:
                    conn.execute("ROLLBACK")
                    raise
        except sqlite3.OperationalError as exc:
            if getattr(exc, "sqlite_errorcode", None) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                emit("storage.busy", outcome="esgotado")
            raise
        finally:
            emit("storage.unit", outcome=outcome, duration_ms=(time.monotonic()-start)*1000)

    async def aread(self, callback: Callable[[sqlite3.Connection], T]) -> T:
        return await asyncio.to_thread(self.read, callback)

    async def awrite(self, callback: Callable[[sqlite3.Connection], T]) -> T:
        # Cancellation must not release a session lock while its thread can still commit.
        task = asyncio.create_task(asyncio.to_thread(self.write, callback))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            await task
            raise

    def sources(self) -> dict:
        result = {}
        for name in ("apartamentos", "areas", "reservas", "visitantes"):
            result[name] = json.loads((self.settings.data_dir / f"{name}.json").read_text())
        for row in result["reservas"] + result["visitantes"]:
            if date.fromisoformat(row["data"]).isoformat() != row["data"]:
                raise ValueError("Data inicial inválida")
        return result

    def seed(self, conn: sqlite3.Connection, sources: dict) -> None:
        conn.executemany("INSERT INTO apartamentos VALUES (:numero,:morador)", sources["apartamentos"])
        conn.executemany("INSERT INTO areas VALUES (?,?,?)", [
            (r["id"], r["nome"], int(Decimal(str(r["taxa"]))*100)) for r in sources["areas"]
        ])
        conn.executemany("INSERT INTO reservas(codigo,apartamento,area,data,status) VALUES (:codigo,:apartamento,:area,:data,'ativa')", sources["reservas"])
        conn.executemany("INSERT INTO visitantes(id,apartamento,nome,data) VALUES (?,?,?,?)", [
            (f"inicial-{i}", r["apartamento"], r["nome"], r["data"]) for i, r in enumerate(sources["visitantes"])
        ])
        self.fault("seed")

    def initialize(self) -> None:
        Path(self.settings.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA)
        def load(conn):
            version = conn.execute("SELECT version FROM schema_version").fetchall()
            if version and [r[0] for r in version] != [1]:
                raise ValueError("Versão de esquema não suportada")
            counts = [conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                      for table in ("apartamentos", "areas", "reservas", "visitantes")]
            if not any(counts):
                self.seed(conn, self.sources())
            else:
                # Reservas e visitantes podem ficar vazios por operações válidas; catálogos não.
                sources = self.sources()
                apartments = [dict(r) for r in conn.execute("SELECT numero,morador FROM apartamentos ORDER BY numero")]
                areas = [dict(r) for r in conn.execute("SELECT * FROM areas ORDER BY id")]
                expected_areas = sorted([dict(id=r["id"], nome=r["nome"], taxa_centavos=int(Decimal(str(r["taxa"]))*100)) for r in sources["areas"]], key=lambda r: r["id"])
                if apartments != sorted(sources["apartamentos"], key=lambda r: r["numero"]) or areas != expected_areas:
                    raise ValueError("Domínio parcialmente populado ou catálogos incompatíveis")
            conn.execute("INSERT OR IGNORE INTO schema_version VALUES (1)")
        self.write(load)

    def reset(self) -> None:
        self.initialize()
        sources = self.sources()
        def restore(conn):
            for table in ("sessoes", "visitantes", "reservas", "areas", "apartamentos"):
                conn.execute(f"DELETE FROM {table}")
            self.fault("reset_deleted")
            self.seed(conn, sources)
        self.write(restore)

    @staticmethod
    def apartment(conn: sqlite3.Connection, numero: str) -> None:
        if not conn.execute("SELECT 1 FROM apartamentos WHERE numero=?", (numero,)).fetchone():
            raise LookupError("Apartamento inexistente")

    @staticmethod
    def session_row(conn: sqlite3.Connection, session_id: str):
        row = conn.execute("SELECT * FROM sessoes WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise LookupError("Sessão inexistente")
        return row

    @staticmethod
    def reservations(conn: sqlite3.Connection, numero: str) -> list[dict]:
        Database.apartment(conn, numero)
        return [dict(r) for r in conn.execute("SELECT codigo,area,data FROM reservas WHERE apartamento=? AND status='ativa' ORDER BY data,codigo", (numero,))]

    @staticmethod
    def visitors(conn: sqlite3.Connection, numero: str) -> list[dict]:
        Database.apartment(conn, numero)
        return [dict(r) for r in conn.execute("SELECT nome,data FROM visitantes WHERE apartamento=? ORDER BY data,id", (numero,))]

    @staticmethod
    def pending(conn: sqlite3.Connection, session_id: str) -> list[dict]:
        Database.session_row(conn, session_id)
        return [dict(id=r["id"], acao=r["acao"], detalhes=json.loads(r["detalhes"])) for r in conn.execute("SELECT * FROM confirmacoes WHERE session_id=? AND estado='pendente' ORDER BY rowid", (session_id,))]
