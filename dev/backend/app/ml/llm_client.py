import json
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from app.ml import config

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class ChatResult(BaseModel):
    parsed: dict[str, Any] | None
    raw_text: str | None


class LLMConfig:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_s: float = config.LLM_TIMEOUT_S,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout_s = timeout_s


def planner_config(base_url: str | None = None, model: str | None = None) -> LLMConfig:
    return LLMConfig(
        base_url=base_url or os.environ.get("ML_PLANNER_BASE_URL", config.PLANNER_BASE_URL_DEFAULT),
        model=model or os.environ.get("ML_PLANNER_MODEL", config.PLANNER_MODEL_DEFAULT),
    )


def actor_config(base_url: str | None = None, model: str | None = None) -> LLMConfig:
    return LLMConfig(
        base_url=base_url or os.environ.get("ML_ACTOR_BASE_URL", config.ACTOR_BASE_URL_DEFAULT),
        model=model or os.environ.get("ML_ACTOR_MODEL", config.ACTOR_MODEL_DEFAULT),
    )


def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


class ChatClient:
    def __init__(self, llm_config: LLMConfig, client: httpx.AsyncClient) -> None:
        self._config = llm_config
        self._client = client

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def base_url(self) -> str:
        return self._config.base_url

    async def emit_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            },
            "temperature": temperature,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        body = await self._send(payload)
        raw_text = _extract_content(body)
        return ChatResult(parsed=_parse_json_object(raw_text), raw_text=raw_text)

    async def _send(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        try:
            response = await self._client.post(
                f"{self._config.base_url}/chat/completions",
                json=payload,
                timeout=self._config.timeout_s,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        body: dict[str, Any] = response.json()
        return body


def _extract_content(body: dict[str, Any] | None) -> str | None:
    if body is None:
        return None
    choices = body.get("choices") or []
    if not choices:
        return None
    content = (choices[0].get("message") or {}).get("content")
    return content if isinstance(content, str) else None


def _parse_json_object(raw_text: str | None) -> dict[str, Any] | None:
    if raw_text is None:
        return None
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
