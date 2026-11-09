"""ElevenLabs TTS provider adapter."""
import httpx
import aiofiles
import os
from app.services.ai.base import TTSProvider, TTSResponse
from app.core.config import settings

_COST_PER_CHAR = 0.00003  # ~$30 per 1M characters (Starter plan)


class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self):
        self._base = "https://api.elevenlabs.io/v1"
        self._key = settings.ELEVENLABS_API_KEY

    async def synthesize(self, text: str, voice_id: str, language: str = "en-US") -> TTSResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base}/text-to-speech/{voice_id}",
                headers={"xi-api-key": self._key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.6, "similarity_boost": 0.8},
                },
            )
            resp.raise_for_status()
            audio_bytes = resp.content

        # Save to local storage temporarily
        file_key = f"audio/tts/{voice_id}_{hash(text)}.mp3"
        local_path = os.path.join(settings.LOCAL_STORAGE_PATH, file_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        async with aiofiles.open(local_path, "wb") as f:
            await f.write(audio_bytes)

        duration = len(audio_bytes) / (128 * 1024 / 8)  # rough estimate at 128kbps
        cost = len(text) * _COST_PER_CHAR

        return TTSResponse(
            audio_url=f"/storage/{file_key}",
            duration_seconds=duration,
            provider="elevenlabs",
            voice_id=voice_id,
            cost_usd=cost,
            file_key=file_key,
        )
