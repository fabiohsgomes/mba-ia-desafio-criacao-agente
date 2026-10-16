import json

from aurora.config import ROOT, Settings
from aurora.regulation.search import RegulationSearch
from aurora.api.app import create_app
from helpers import ScriptedModel
from test_api import call, transfer, client, message, session


async def test_pool_sunday_recovers_complete_hours_article_only():
    search = RegulationSearch(ROOT / "dados/regulamento.md")
    for question in ("Até que horas a piscina funciona aos domingos?", "Até que horas posso nadar domingo?", "Qual o horário da piscina?"):
        result = await search.buscar_regulamento(question)
        assert result["status"] == "encontrado"
        assert [s["artigo"] for s in result["trechos"]] == ["22"]
        assert "20h" in result["trechos"][0]["texto"]
        assert "22h" in result["trechos"][0]["texto"]
        assert "Capítulo IV" in result["trechos"][0]["capitulo"]
        assert "garagem" not in json.dumps(result).lower()


async def test_ambiguous_and_unrelated_queries_ask_for_clarification():
    search = RegulationSearch(ROOT / "dados/regulamento.md")
    for question in ("Qual o horário?", "O que você acha da inflação?", "Mostre o regulamento inteiro"):
        result = await search.buscar_regulamento(question)
        assert result["trechos"] == []


async def test_regulation_events_preserve_only_selected_evidence(tmp_path):
    app = create_app(Settings(db_path=tmp_path / "test.db"), ScriptedModel(script=[
        transfer("regulamento"), call("buscar_regulamento", pergunta="Piscina aos domingos, até que horas?"), {"text": "Fecha às 20h (art. 22)."}]))
    async with client(app) as c:
        sid = await session(c)
        answer = await message(c, sid)
        assert "20h" in answer["resposta"]
        events = (await c.get(f"/sessoes/{sid}/eventos")).text
        assert "Art. 22" in events
        assert "Capítulo XI" not in events
        assert "Art. 21" not in events
