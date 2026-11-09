"""Anthropic Claude LLM provider.

Uses the Messages API via the official anthropic-sdk-python.
Docs: https://docs.anthropic.com/en/api/messages
"""
from typing import Optional
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.base import LLMProvider, LLMResponse
from app.core.config import settings


# Input/output token pricing (USD per 1M tokens) — Claude Sonnet 4
_PRICING = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
    "claude-opus-4-5": {"input": 15.0, "output": 75.0},
}
_DEFAULT_MODEL = "claude-sonnet-4-5"


class AnthropicLLMProvider(LLMProvider):
    """Claude-based LLM provider for script and research generation."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = getattr(settings, "ANTHROPIC_MODEL", _DEFAULT_MODEL)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]

        sys_prompt = system or (
            "You are a creative children's content specialist who writes original, "
            "engaging educational content for kids aged 2-8. Never copy or reference "
            "existing shows. Keep all content positive and age-appropriate."
        )
        if json_mode:
            sys_prompt += "\n\nRespond with valid JSON only. No markdown fences."

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=sys_prompt,
            messages=messages,
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._calc_cost(input_tokens, output_tokens),
            provider="anthropic",
            metadata={"model": self.model, "stop_reason": response.stop_reason},
        )

    def _calc_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = _PRICING.get(self.model, _PRICING[_DEFAULT_MODEL])
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        return round(cost, 6)
