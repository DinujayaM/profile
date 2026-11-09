"""ElevenLabs TTS provider — complete implementation.

API docs: https://elevenlabs.io/docs/api-reference
Supports:
  - Text-to-speech (v1/text-to-speech)
  - Streaming for long narrations
  - Voice cloning / custom voice IDs
  - Cost tracking per character
"""
from pathlib import Path
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai.base import TTSProvider, TTSResponse
from app.core.config import settings


# Default voices that are child-friendly
CHILD_VOICES = {
    "narrator_female": "EXAVITQu4vr4xnSDxMaL",   # Bella
    "narrator_male": "VR6AewLTigWG4xSOukaG",       # Arnold
    "child_girl": "jBpfuIE2acCO8z3wKNLl",          # Gigi
    "child_boy": "jsCqWAovK2LkecY7zXl4",            # Freya (androgynous)
}


class ElevenLabsTTSProvider(TTSProvider):
    """ElevenLabs text-to-speech with streaming support."""

    BASE_URL = "https://api.elevenlabs.io/v1"
    COST_PER_CHAR = 0.00003  # ~$30 per 1M characters (Creator plan)

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        voice_name: str = "narrator_female",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        output_path: Optional[str] = None,
    ) -> TTSResponse:
        vid = voice_id or CHILD_VOICES.get(voice_name, CHILD_VOICES["narrator_female"])

        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
            },
        }

        audio_bytes = await self._stream_audio(vid, payload)

        local_path = None
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            local_path = output_path

        char_count = len(text)
        return TTSResponse(
            audio_url=None,
            local_path=local_path,
            duration_seconds=self._estimate_duration(char_count),
            cost_usd=round(char_count * self.COST_PER_CHAR, 6),
            provider="elevenlabs",
            metadata={
                "voice_id": vid,
                "voice_name": voice_name,
                "model": "eleven_turbo_v2_5",
                "char_count": char_count,
            },
        )

    async def _stream_audio(self, voice_id: str, payload: dict) -> bytes:
        """Stream audio and collect into bytes."""
        chunks = []
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/text-to-speech/{voice_id}/stream",
                headers=self.headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    chunks.append(chunk)
        return b"".join(chunks)

    async def list_voices(self) -> list[dict]:
        """Return available voices from the API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
            )
            resp.raise_for_status()
            return resp.json().get("voices", [])

    def _estimate_duration(self, char_count: int) -> float:
        # Average speech rate ~150 words/min, ~5 chars/word
        words = char_count / 5
        return round(words / 150 * 60, 1)
