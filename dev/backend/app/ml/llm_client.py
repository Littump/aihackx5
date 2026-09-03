import json
import os
from pathlib import Path
from typing import Any

import httpx

from app.ml import config

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class LLMConfig:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = config.LLM_TIMEOUT_S,
    ) -> None:
        self.base_url = base_url or os.environ.get("ML_LLM_BASE_URL", config.LLM_BASE_URL_DEFAULT)
        self.model = model or os.environ.get("ML_LLM_MODEL", config.LLM_MODEL_DEFAULT)
        self.timeout_s = timeout_s


def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


class QwenClient:
    def __init__(self, llm_config: LLMConfig, client: httpx.AsyncClient) -> None:
        self._config = llm_config
        self._client = client

    async def emit_tool(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_name: str,
        input_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 700,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": "Emit structured output that matches the schema exactly.",
                        "parameters": input_schema,
                    },
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": tool_name}},
            "temperature": temperature,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        arguments = await self._post(payload)
        return arguments

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        try:
            response = await self._client.post(
                f"{self._config.base_url}/chat/completions",
                json=payload,
                timeout=self._config.timeout_s,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        return _extract_tool_arguments(response.json())


def _extract_tool_arguments(body: dict[str, Any]) -> dict[str, Any] | None:
    choices = body.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return None
    raw_arguments = tool_calls[0].get("function", {}).get("arguments")
    if not isinstance(raw_arguments, str):
        return None
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
