import asyncio

import httpx
import pytest
from google.genai import types

from aurora.agents.model import AuroraGemini
from aurora.api.app import create_app
from aurora.config import Settings
from test_api import client, session


@pytest.mark.parametrize("status", [429, 503])
async def test_sdk_transport_makes_exactly_one_attempt(tmp_path, status):
    calls = 0
    async def transport(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={"error": {"code": status, "message": "temporary failure", "status": "UNAVAILABLE"}})
    model = AuroraGemini(model="gemini-3.8-flash", client_kwargs={"api_key": "test-key", "http_options": types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1), async_client_args={"transport": httpx.MockTransport(transport)})})
    app = create_app(Settings(db_path=tmp_path / "test.db"), model)
    try:
        async with client(app) as c:
            sid = await session(c)
            response = await c.post(f"/sessoes/{sid}/mensagens", json={"texto": "Reserve a quadra"})
            assert response.status_code == 502
            assert calls == 1
    finally:
        await model.api_client.aio.aclose()
        model.api_client.close()


async def test_inference_timeout_cancels_transport_without_late_effects(tmp_path):
    calls, cancelled = 0, False
    async def transport(request):
        nonlocal calls, cancelled
        calls += 1
        try:
            await asyncio.sleep(.2)
        except asyncio.CancelledError:
            cancelled = True
            raise
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": "Tarde demais"}]}}]})
    model = AuroraGemini(model="gemini-3.8-flash", inference_timeout=.02,
                        client_kwargs={"api_key": "test-key", "http_options": types.HttpOptions(
                            retry_options=types.HttpRetryOptions(attempts=1), async_client_args={"transport": httpx.MockTransport(transport)})})
    app = create_app(Settings(db_path=tmp_path / "test.db"), model)
    try:
        async with client(app) as c:
            sid = await session(c)
            response = await c.post(f"/sessoes/{sid}/mensagens", json={"texto": "Reserve a quadra"})
            assert response.status_code == 504
            assert calls == 1 and cancelled
            before = (await c.get(f"/sessoes/{sid}/eventos")).json()
            await asyncio.sleep(.25)
            assert (await c.get(f"/sessoes/{sid}/eventos")).json() == before
            assert len((await c.get("/apartamentos/101/reservas")).json()) == 1
    finally:
        await model.api_client.aio.aclose()
        model.api_client.close()
