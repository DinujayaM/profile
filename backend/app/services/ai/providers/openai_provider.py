"""OpenAI provider adapter for LLM and image generation."""
import httpx
from app.services.ai.base import LLMProvider, LLMResponse, ImageProvider, ImageResponse
from app.core.config import settings

# Cost per 1k tokens (approximate, update as OpenAI changes pricing)
_LLM_COST = {"gpt-4o": {"input": 0.0025, "output": 0.01}, "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}}
_IMAGE_COST = {"dall-e-3": {"1024x1024": 0.040, "1792x1024": 0.080, "1024x1792": 0.080}}


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self._base = "https://api.openai.com/v1"
        self._key = settings.OPENAI_API_KEY
        self._model = settings.LLM_MODEL

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base}/chat/completions",
                headers={"Authorization": f"Bearer {self._key}"},
                json={"model": self._model, "messages": messages, "max_tokens": max_tokens},
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data["usage"]
        cost_table = _LLM_COST.get(self._model, {"input": 0.003, "output": 0.015})
        cost = (usage["prompt_tokens"] * cost_table["input"] + usage["completion_tokens"] * cost_table["output"]) / 1000

        return LLMResponse(
            content=choice,
            model=self._model,
            provider="openai",
            input_tokens=usage["prompt_tokens"],
            output_tokens=usage["completion_tokens"],
            cost_usd=cost,
        )


class OpenAIImageProvider(ImageProvider):
    def __init__(self):
        self._base = "https://api.openai.com/v1"
        self._key = settings.OPENAI_API_KEY
        self._model = settings.IMAGE_MODEL

    async def generate(self, prompt: str, width: int = 1920, height: int = 1080) -> ImageResponse:
        # DALL-E 3 supports 1024x1024, 1792x1024, 1024x1792
        size = "1792x1024" if width > height else ("1024x1792" if height > width else "1024x1024")

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base}/images/generations",
                headers={"Authorization": f"Bearer {self._key}"},
                json={"model": self._model, "prompt": prompt, "n": 1, "size": size, "quality": "standard"},
            )
            resp.raise_for_status()
            data = resp.json()

        image_data = data["data"][0]
        cost = _IMAGE_COST.get(self._model, {}).get(size, 0.04)

        return ImageResponse(
            url=image_data["url"],
            provider="openai",
            model=self._model,
            cost_usd=cost,
            width=width,
            height=height,
            revised_prompt=image_data.get("revised_prompt"),
        )
