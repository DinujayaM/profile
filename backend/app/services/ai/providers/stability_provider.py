"""Stability AI image generation provider.

Uses Stable Diffusion 3.5 via the Stability AI REST API.
Docs: https://platform.stability.ai/docs/api-reference
"""
import base64
from pathlib import Path
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.base import ImageProvider, ImageResponse
from app.core.config import settings


class StabilityImageProvider(ImageProvider):
    """Stability AI Stable Diffusion 3.5 image generation."""

    BASE_URL = "https://api.stability.ai/v2beta"

    def __init__(self):
        self.api_key = settings.STABILITY_API_KEY
        self.headers = {
            "authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        output_path: Optional[str] = None,
    ) -> ImageResponse:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE_URL}/stable-image/generate/sd3",
                headers=self.headers,
                data={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model": "sd3.5-large",
                    "output_format": "png",
                    "aspect_ratio": self._aspect_ratio(width, height),
                    "mode": "text-to-image",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        image_b64 = data.get("image", "")
        image_bytes = base64.b64decode(image_b64)

        local_path = None
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            local_path = output_path

        return ImageResponse(
            image_url=None,
            image_b64=image_b64,
            local_path=local_path,
            width=width,
            height=height,
            cost_usd=self._estimate_cost(),
            provider="stability",
            metadata={"model": "sd3.5-large", "finish_reason": data.get("finish_reason")},
        )

    def _aspect_ratio(self, width: int, height: int) -> str:
        ratio = width / height
        if ratio >= 1.7:
            return "16:9"
        if ratio >= 1.3:
            return "4:3"
        if ratio <= 0.6:
            return "9:16"
        return "1:1"

    def _estimate_cost(self) -> float:
        # SD3.5 Large: ~$0.065 per image
        return 0.065
