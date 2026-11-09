"""Suno AI music generation provider.

Uses the unofficial Suno API wrapper. When SUNO_API_KEY is not set, falls
back to the mock provider automatically via the factory.

NOTE: Suno does not currently offer an official public API. This adapter
targets the community API at https://github.com/gcui-art/suno-api which
wraps the Suno web service. Replace BASE_URL and auth when an official API
is released.
"""
import asyncio
import time
from pathlib import Path
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.base import MusicProvider, MusicResponse
from app.core.config import settings


class SunoMusicProvider(MusicProvider):
    """Suno AI background music generation."""

    BASE_URL = "https://api.sunoapi.com"  # community API endpoint
    POLL_INTERVAL = 10
    MAX_WAIT = 300  # 5 minutes

    def __init__(self):
        self.api_key = settings.SUNO_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=30))
    async def generate_music(
        self,
        prompt: str,
        duration_seconds: int = 30,
        instrumental: bool = True,
        output_path: Optional[str] = None,
    ) -> MusicResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/generate",
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "make_instrumental": instrumental,
                    "wait_audio": False,
                },
            )
            resp.raise_for_status()
            ids = [item["id"] for item in resp.json()]

        audio_url = await self._poll_complete(ids[0])

        local_path = None
        if output_path and audio_url:
            local_path = await self._download(audio_url, output_path)

        return MusicResponse(
            audio_url=audio_url,
            local_path=local_path,
            duration_seconds=duration_seconds,
            cost_usd=self._estimate_cost(duration_seconds),
            provider="suno",
            metadata={"clip_id": ids[0], "instrumental": instrumental},
        )

    async def _poll_complete(self, clip_id: str) -> str:
        deadline = time.time() + self.MAX_WAIT
        async with httpx.AsyncClient(timeout=30) as client:
            while time.time() < deadline:
                await asyncio.sleep(self.POLL_INTERVAL)
                resp = await client.get(
                    f"{self.BASE_URL}/api/get?ids={clip_id}",
                    headers=self.headers,
                )
                resp.raise_for_status()
                items = resp.json()
                if items and items[0].get("status") == "complete":
                    return items[0]["audio_url"]
                if items and items[0].get("status") in ("error", "failed"):
                    raise RuntimeError(f"Suno clip {clip_id} failed")
        raise TimeoutError(f"Suno clip {clip_id} not ready within {self.MAX_WAIT}s")

    async def _download(self, url: str, path: str) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
        return path

    def _estimate_cost(self, duration_seconds: int) -> float:
        # Approximate: $0.01 per generated clip
        return 0.01
