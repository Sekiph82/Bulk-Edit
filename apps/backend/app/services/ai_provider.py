"""
AI provider abstraction. Default is 'mock' — no API keys required.
Switch via AI_PROVIDER env var: mock | openai | anthropic
"""
from __future__ import annotations

import json
from typing import Any

from app.core.config import settings


class AIProviderError(Exception):
    pass


class MockProvider:
    async def generate_json(self, prompt: str, schema_name: str, context: dict) -> dict:
        listing_title = context.get("title", "Sample Listing")
        if schema_name == "title":
            return {
                "suggested_title": f"{listing_title} — Handcrafted Quality",
                "reasoning": "Added quality descriptor to improve SEO.",
            }
        if schema_name == "description":
            return {
                "suggested_description": (
                    f"Discover {listing_title}. Handcrafted with care and attention to detail. "
                    "Perfect as a gift or for personal use. Ships within 3-5 business days."
                ),
                "reasoning": "Added benefit-oriented language and shipping info.",
            }
        if schema_name == "tags":
            return {
                "suggested_tags": [
                    "handmade",
                    "unique gift",
                    "etsy seller",
                    "handcrafted",
                    "quality",
                    "artisan",
                    "shop small",
                    "made with love",
                    "original design",
                    "best seller",
                ],
                "reasoning": "Tags optimized for Etsy search visibility.",
            }
        if schema_name == "alt_text":
            return {
                "suggested_alt_text": f"Close-up photo of {listing_title} showing details and craftsmanship.",
                "reasoning": "Descriptive alt text improves accessibility and image SEO.",
            }
        if schema_name == "seo_score":
            return {
                "score": 72,
                "title_score": 70,
                "description_score": 68,
                "tags_score": 80,
                "issues": [
                    "Title could include primary keyword earlier",
                    "Description missing key features in first sentence",
                ],
                "suggestions": [
                    "Move primary keyword to start of title",
                    "Add 2-3 more long-tail tags",
                ],
            }
        return {"result": f"mock result for {schema_name}", "reasoning": "mock"}


class OpenAIProvider:
    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError as exc:
            raise AIProviderError("openai package not installed") from exc
        if not settings.is_openai_configured():
            raise AIProviderError("OPENAI_API_KEY not configured")
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        )

    async def generate_json(self, prompt: str, schema_name: str, context: dict) -> dict:
        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": _system_prompt(schema_name)},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as exc:
            raise AIProviderError(f"OpenAI request failed: {type(exc).__name__}") from exc


class AnthropicProvider:
    def __init__(self) -> None:
        try:
            import anthropic as _anthropic  # type: ignore
        except ImportError as exc:
            raise AIProviderError("anthropic package not installed") from exc
        if not settings.is_anthropic_configured():
            raise AIProviderError("ANTHROPIC_API_KEY not configured")
        self._client = _anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        )

    async def generate_json(self, prompt: str, schema_name: str, context: dict) -> dict:
        try:
            import anthropic as _anthropic  # type: ignore
            message = await self._client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1024,
                system=_system_prompt(schema_name),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text if message.content else "{}"
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]
            return json.loads(raw)
        except Exception as exc:
            raise AIProviderError(f"Anthropic request failed: {type(exc).__name__}") from exc


def _system_prompt(schema_name: str) -> str:
    base = (
        "You are an expert Etsy SEO assistant helping sellers optimize their listings. "
        "Respond ONLY with valid JSON matching the requested schema. No markdown, no extra text."
    )
    hints: dict[str, str] = {
        "title": ' Schema: {"suggested_title": string, "reasoning": string}',
        "description": ' Schema: {"suggested_description": string, "reasoning": string}',
        "tags": ' Schema: {"suggested_tags": [up to 13 strings, each <=20 chars], "reasoning": string}',
        "alt_text": ' Schema: {"suggested_alt_text": string, "reasoning": string}',
        "seo_score": (
            ' Schema: {"score": 0-100, "title_score": 0-100, "description_score": 0-100,'
            ' "tags_score": 0-100, "issues": [string], "suggestions": [string]}'
        ),
    }
    return base + hints.get(schema_name, "")


def get_provider() -> Any:
    p = settings.AI_PROVIDER.lower()
    if p == "openai":
        return OpenAIProvider()
    if p == "anthropic":
        return AnthropicProvider()
    return MockProvider()
