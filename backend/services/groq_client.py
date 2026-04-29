from __future__ import annotations

import json
from typing import Any

from groq import Groq

from app.core.config import get_settings


class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        if self.settings.groq_api_key:
            try:
                self.client = Groq(api_key=self.settings.groq_api_key)
            except TypeError:
                # Older or incompatible Groq/httpx combinations can fail during client creation.
                # The rest of the app falls back safely when this happens.
                self.client = None
            except Exception:
                self.client = None

    def _messages(self, system: str, user: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def complete(self, *, system: str, user: str, json_mode: bool = False, temperature: float | None = None) -> str:
        if self.client is None:
            return "{}" if json_mode else "Groq API key is missing."

        kwargs: dict[str, Any] = {
            "model": self.settings.resolved_groq_model,
            "messages": self._messages(system, user),
            "temperature": self.settings.groq_temperature if temperature is None else temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def complete_json(self, *, system: str, user: str, temperature: float | None = None) -> dict[str, Any]:
        content = self.complete(system=system, user=user, json_mode=True, temperature=temperature)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}
