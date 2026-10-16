"""Dublê somente da inferência: Runner, transferências, tools e SQLite são reais."""
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field


class ScriptedModel(BaseLlm):
    model: str = "scripted"
    script: list[dict] = Field(default_factory=list)
    calls: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.calls += 1
        if not self.script:
            raise AssertionError("Inferência inesperada")
        step = self.script.pop(0)
        if "error" in step:
            raise step["error"]
        if "sleep" in step:
            import asyncio
            await asyncio.sleep(step["sleep"])
        if "calls" in step:
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=c["call"], args=c.get("args", {}))) for c in step["calls"]]))
            return
        if "call" in step:
            part = types.Part(function_call=types.FunctionCall(name=step["call"], args=step.get("args", {})))
        else:
            part = types.Part(text=step.get("text", "Concluído."))
        yield LlmResponse(content=types.Content(role="model", parts=[part]))
