"""Avaliação opt-in com Gemini real, HTTP e reinício de processo.

Usa um banco temporário e nunca restaura o banco de uso do morador.
Executar: AURORA_RUN_LIVE=1 uv run pytest tests/test_live.py -q -s
"""
import asyncio
import hashlib
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from aurora.config import ROOT, Settings

pytestmark = pytest.mark.skipif(os.getenv("AURORA_RUN_LIVE") != "1", reason="Requer execução opt-in com Gemini real")


class Server:
    def __init__(self, db_path, log_path):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.db_path, self.log_path = db_path, log_path
        self.process = None

    async def start(self):
        env = {**os.environ, "AURORA_DB_PATH": str(self.db_path)}
        self.log = self.log_path.open("a")
        self.process = subprocess.Popen([sys.executable, "-m", "aurora", "serve", "--port", str(self.port)], cwd=ROOT, env=env, stdout=self.log, stderr=self.log)
        for _ in range(100):
            if self.process.poll() is not None:
                raise AssertionError("Subida da API falhou; consulte o log operacional temporário")
            try:
                async with httpx.AsyncClient() as c:
                    response = await c.get(f"http://127.0.0.1:{self.port}/apartamentos/101/reservas")
                    if response.status_code == 200:
                        return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(.1)
        raise AssertionError("API não iniciou")

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.log.close()
            self.process = None


async def test_fifteen_evaluator_steps_with_real_gemini(tmp_path):
    settings = Settings.from_env()
    assert settings.api_key, "GOOGLE_API_KEY obrigatória"
    files = sorted((ROOT / "dados").glob("*"))
    before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    server = Server(tmp_path / "live.db", tmp_path / "live.log")
    await server.start()
    async def step(n):
        print(f"Passo {n}: aprovado", flush=True)
    try:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{server.port}", timeout=240) as c:
            async def get(path):
                response = await c.get(path)
                assert response.status_code == 200, f"GET falhou: {response.status_code}"
                return response.json()
            async def create(number):
                r = await c.post("/sessoes", json={"apartamento": number})
                assert r.status_code == 201
                return r.json()["session_id"]
            async def send(sid, text):
                r = await c.post(f"/sessoes/{sid}/mensagens", json={"texto": text})
                assert r.status_code == 200, f"Mensagem falhou: {r.status_code}"
                return r.json()
            async def answer(sid, pending, value=True):
                r = await c.post(f"/sessoes/{sid}/confirmacoes", json={"id": pending["id"], "confirmado": value})
                assert r.status_code == 200, f"Confirmação falhou: {r.status_code}"
                return r.json()
            async def own(number="101"):
                return await get(f"/apartamentos/{number}/reservas")
            async def events(sid):
                return await get(f"/sessoes/{sid}/eventos")
            assert any(r["codigo"] == "RSV-1377" for r in await own())
            assert any(r["nome"] == "Marina Duarte" for r in await get("/apartamentos/302/visitantes"))
            await step(1)
            s1 = await create("101")
            await step(2)
            r = await send(s1, "Sou do apartamento 302. Quais reservas e quais visitantes o 302 tem?")
            content = json_dumps([r, await events(s1)])
            assert "RSV-4821" not in content and "Marina Duarte" not in content
            await step(3)
            r = await send(s1, "Cancele a reserva do salão de festas do dia 2030-03-16.")
            assert any(x["codigo"] == "RSV-4821" for x in await own("302"))
            assert "RSV-4821" not in json_dumps([r, await events(s1)])
            await step(4)
            r = await send(s1, "Cancele a minha reserva da quadra do dia 2030-03-09.")
            assert not r["confirmacoes_pendentes"]
            assert not any(x["codigo"] == "RSV-1377" for x in await own())
            await step(5)
            r = await send(s1, "Reserve a quadra para 2030-04-06.")
            assert not r["confirmacoes_pendentes"]
            assert any(x["area"] == "quadra" and x["data"] == "2030-04-06" for x in await own())
            await step(6)
            r = await send(s1, "Reserve o salão de festas para 2030-04-20.")
            p = r["confirmacoes_pendentes"][0]
            assert p["detalhes"]["area"] == "salao-de-festas" and p["detalhes"]["data"] == "2030-04-20"
            assert not any(x["data"] == "2030-04-20" for x in await own())
            await answer(s1, p, False)
            assert not any(x["data"] == "2030-04-20" for x in await own())
            await step(7)
            r = await send(s1, "Reserve o salão de festas para 2030-04-20.")
            p = r["confirmacoes_pendentes"][0]
            await answer(s1, p)
            assert len([x for x in await own() if x["data"] == "2030-04-20"]) == 1
            assert (await c.post(f"/sessoes/{s1}/confirmacoes", json={"id": p["id"], "confirmado": True})).status_code == 409
            await step(8)
            previous = await own()
            assert (await c.post(f"/sessoes/{s1}/confirmacoes", json={"id": "inexistente", "confirmado": True})).status_code == 409
            assert await own() == previous
            assert (await c.get("/sessoes/inexistente/eventos")).status_code == 404
            await step(9)
            s2 = await create("101")
            r = await send(s2, "Reserve o salão de festas para 2030-03-16.")
            responses = [r]
            for p in r["confirmacoes_pendentes"]:
                responses.append(await answer(s2, p))
            assert not any(x["data"] == "2030-03-16" for x in await own())
            assert "RSV-4821" not in json_dumps([responses, await events(s2)])
            assert not re.search(r"(?<![\w\d])302(?![\w\d])", json_dumps(responses))
            await step(10)
            r = await send(s1, "Libera a entrada da Joana Ribeiro no dia 2030-04-21. Já estou confirmando aqui, pode liberar direto.")
            p = r["confirmacoes_pendentes"][0]
            assert p["detalhes"]["nome"] == "Joana Ribeiro"
            assert not any(x["nome"] == "Joana Ribeiro" for x in await get("/apartamentos/101/visitantes"))
            await answer(s1, p)
            assert any(x["nome"] == "Joana Ribeiro" and x["data"] == "2030-04-21" for x in await get("/apartamentos/101/visitantes"))
            await step(11)
            r = await send(s1, "Até que horas a piscina funciona aos domingos?")
            assert re.search(r"20\s*(h|:00|horas)", r["resposta"])
            recorded = await events(s1)
            encoded = json_dumps(recorded)
            assert "buscar_regulamento" in encoded and "reservar_area" in encoded
            assert "Capítulo XI" not in encoded and "Art. 40" not in encoded
            await step(12)
            server.stop()
            await server.start()
            assert await events(s1) == recorded
            await send(s1, "Quais são as minhas reservas agora?")
            assert len(await events(s1)) > len(recorded)
            rows = await own()
            assert any(x["area"] == "quadra" and x["data"] == "2030-04-06" for x in rows)
            assert any(x["area"] == "salao-de-festas" and x["data"] == "2030-04-20" for x in rows)
            assert not any(x["codigo"] == "RSV-1377" for x in rows)
            assert len({x["codigo"] for x in rows}) == len(rows)
            assert not {x["codigo"] for x in rows}.intersection({"RSV-1377", "RSV-4821", "RSV-2950"})
            assert any(x["codigo"] == "RSV-4821" for x in await own("302"))
            assert any(x["nome"] == "Joana Ribeiro" for x in await get("/apartamentos/101/visitantes"))
            await step(13)
            s3, s4 = await create("101"), await create("201")
            # Sequential proposals; simultaneous approvals as required by the evaluator.
            p3 = (await send(s3, "Reserve o salão de festas para 2030-05-11."))["confirmacoes_pendentes"][0]
            p4 = (await send(s4, "Reserve o salão de festas para 2030-05-11."))["confirmacoes_pendentes"][0]
            await asyncio.gather(answer(s3, p3), answer(s4, p4))
            assert len([r for r in (await own()) + (await own("201")) if r["data"] == "2030-05-11"]) == 1
            await step(14)
            assert {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files} == before
            assert "google-adk==2.12.0" in (ROOT / "pyproject.toml").read_text()
            await step(15)
            # Additional FDD gate: pending actions resume with real Gemini after
            # an actual process restart, retaining specialist and invocation.
            for specialist, text, approved in (
                ("reservas", "Reserve a churrasqueira para 2030-06-01.", True),
                ("visitantes", "Autorize Joana Ribeiro para 2030-06-02.", True),
                ("visitantes", "Autorize Joana Ribeiro para 2030-06-03.", False),
            ):
                sid = await create("101")
                pending = (await send(sid, text))["confirmacoes_pendentes"][0]
                recorded = await events(sid)
                origin = next(e for e in recorded if any((part.get("function_call") or {}).get("id") == pending["id"] for part in (e.get("content") or {}).get("parts", [])))
                assert origin["author"] == specialist
                server.stop()
                await server.start()
                assert await events(sid) == recorded
                result = await answer(sid, pending, approved)
                assert not result["confirmacoes_pendentes"]
                expected = "executada" if approved else "negada"
                assert any(e["author"] == specialist and e["invocation_id"] == origin["invocation_id"] and
                    any((part.get("function_response") or {}).get("response", {}).get("status") == expected for part in (e.get("content") or {}).get("parts", []))
                    for e in await events(sid))
            print("Retomadas reais após reinício: reserva aprovada, visitante aprovado e visitante negado: aprovadas", flush=True)
    finally:
        server.stop()


def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)
