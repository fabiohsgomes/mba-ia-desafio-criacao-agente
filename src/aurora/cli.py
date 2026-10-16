import argparse
import asyncio
import json
import logging

from aurora.config import Settings
from aurora.observability import configure
from aurora.storage.database import Database


def main():
    parser = argparse.ArgumentParser(description="Assistente do Residencial Aurora")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="API local, um worker")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    commands.add_parser("reset", help="Restaura o domínio e limpa sessões atomicamente; execute com a API parada")
    commands.add_parser("probe", help="Uma chamada real ao modelo configurado; sem retries")
    args = parser.parse_args()
    configure()
    try:
        settings = Settings.from_env()
        if args.command == "reset":
            Database(settings).reset()
            print("Dados restaurados; sessões e confirmações removidas.")
        elif args.command == "probe":
            asyncio.run(probe(settings))
        else:
            import uvicorn
            from aurora.api.app import create_app
            uvicorn.run(create_app(settings), host=args.host, port=args.port, workers=1, access_log=False, log_config=None)
    except Exception as exc:
        print(json.dumps({"erro": "Falha na operação", "classe": type(exc).__name__}))
        raise SystemExit(1) from None


async def probe(settings):
    from aurora.agents.model import gemini
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types
    model = gemini(settings)
    try:
        request = LlmRequest(model=settings.model, contents=[types.Content(role="user", parts=[types.Part(text="Responda apenas OK.")])])
        async for _ in model.generate_content_async(request):
            pass
        print("Acesso ao modelo configurado validado (uma inferência).")
    finally:
        await model.api_client.aio.aclose()
        model.api_client.close()
