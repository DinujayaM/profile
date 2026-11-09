"""Runway ML video generation provider.

Runway Gen-3 Alpha API: https://docs.runwayml.com/
Mock adapter is used automatically when RUNWAY_API_KEY is unset.
"""
import asyncio
import time
from pathlib import Path
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.base import VideoClipProvider, VideoClipResponse
from app.core.config import settings


class RunwayVideoProvider(VideoClipProvider):
    """Runway Gen-3 Alpha video clip generation."""

    BASE_URL = "https://api.dev.runwayml.com/v1"
    POLL_INTERVAL = 5  # seconds between status polls
    MAX_WAIT = 600  # 10 minutes max

    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
    async def generate_clip(
        self,
        prompt: str,
        duration_seconds: int = 5,
        image_url: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> VideoClipResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {
                "model": "gen3a_turbo",
                "promptText": prompt,
                "duration": min(duration_seconds, 10),
                "ratio": "1280:768",
                "watermark": False,
            }
            if image_url:
                payload["promptImage"] = image_url

            # Submit generation task
            resp = await client.post(
                f"{self.BASE_URL}/image_to_video",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            task_id = resp.json()["id"]

            # Poll until complete
            video_url = await self._poll_task(client, task_id)

        # Download file if output_path provided
        local_path = None
        if output_path and video_url:
            local_path = await self._download(video_url, output_path)

        return VideoClipResponse(
            clip_url=video_url,
            local_path=local_path,
            duration_seconds=duration_seconds,
            cost_usd=self._estimate_cost(duration_seconds),
            provider="runway",
            metadata={"task_id": task_id, "model": "gen3a_turbo"},
        )

    async def _poll_task(self, client: httpx.AsyncClient, task_id: str) -> str:
        deadline = time.time() + self.MAX_WAIT
        while time.time() < deadline:
            await asyncio.sleep(self.POLL_INTERVAL)
            resp = await client.get(
                f"{self.BASE_URL}/tasks/{task_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status == "SUCCEEDED":
                return data["output"][0]
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Runway task {task_id} ended with status: {status}")
        raise TimeoutError(f"Runway task {task_id} did not complete within {self.MAX_WAIT}s")

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
        # Runway Gen-3 Turbo: ~$0.10 per second of video
        return round(duration_seconds * 0.10, 4)
