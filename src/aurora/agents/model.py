"""Uma tentativa de transporte e timeout por inferência, sem fallback."""
import asyncio
import time

from google.adk.models.google_llm import Gemini
from google.genai import types

from aurora.config import Settings
from aurora.observability import emit, active_agent


class AuroraGemini(Gemini):
    inference_timeout: float = 60

    async def generate_content_async(self, llm_request, stream=False):
        start = time.monotonic()
        outcome = "ok"
        try:
            async with asyncio.timeout(self.inference_timeout):
                responses = [response async for response in super().generate_content_async(llm_request, stream=stream)]
        except BaseException:
            outcome = "falha"
            raise
        finally:
            emit("gemini.infer", agent=active_agent.get(), attempts=1, outcome=outcome, duration_ms=(time.monotonic()-start)*1000)
        for response in responses:
            yield response


def gemini(settings: Settings) -> AuroraGemini:
    if not settings.api_key:
        raise ValueError("Defina GOOGLE_API_KEY no .env")
    return AuroraGemini(model=settings.model, inference_timeout=settings.gemini_timeout,
                        client_kwargs={"api_key": settings.api_key, "http_options": types.HttpOptions(
                            timeout=int(settings.gemini_timeout*1000), retry_options=types.HttpRetryOptions(attempts=1))})
