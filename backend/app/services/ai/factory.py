"""AI provider factory.

Returns the correct provider instance based on settings.*_PROVIDER.
Falls back to mock when the matching API key is absent, so development
works without credentials.
"""
import logging
from app.core.config import settings
from app.services.ai.base import (
    LLMProvider, ImageProvider, TTSProvider, MusicProvider, VideoClipProvider,
)

log = logging.getLogger(__name__)


def _warn_fallback(name: str, reason: str) -> None:
    log.warning("AI provider '%s' unavailable (%s) — using mock", name, reason)


def get_llm_provider() -> LLMProvider:
    from app.services.ai.providers.mock import MockLLMProvider

    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            _warn_fallback("openai-llm", "OPENAI_API_KEY not set")
            return MockLLMProvider()
        from app.services.ai.providers.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider()

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            _warn_fallback("anthropic", "ANTHROPIC_API_KEY not set")
            return MockLLMProvider()
        from app.services.ai.providers.anthropic_provider import AnthropicLLMProvider
        return AnthropicLLMProvider()

    return MockLLMProvider()


def get_image_provider() -> ImageProvider:
    from app.services.ai.providers.mock import MockImageProvider

    provider = settings.IMAGE_PROVIDER.lower()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            _warn_fallback("openai-image", "OPENAI_API_KEY not set")
            return MockImageProvider()
        from app.services.ai.providers.openai_provider import OpenAIImageProvider
        return OpenAIImageProvider()

    if provider == "stability":
        if not settings.STABILITY_API_KEY:
            _warn_fallback("stability", "STABILITY_API_KEY not set")
            return MockImageProvider()
        from app.services.ai.providers.stability_provider import StabilityImageProvider
        return StabilityImageProvider()

    return MockImageProvider()


def get_tts_provider() -> TTSProvider:
    from app.services.ai.providers.mock import MockTTSProvider

    provider = settings.TTS_PROVIDER.lower()
    if provider == "elevenlabs":
        if not settings.ELEVENLABS_API_KEY:
            _warn_fallback("elevenlabs", "ELEVENLABS_API_KEY not set")
            return MockTTSProvider()
        from app.services.ai.providers.elevenlabs_provider import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider()

    return MockTTSProvider()


def get_music_provider() -> MusicProvider:
    from app.services.ai.providers.mock import MockMusicProvider

    provider = settings.MUSIC_PROVIDER.lower()
    if provider == "suno":
        if not settings.SUNO_API_KEY:
            _warn_fallback("suno", "SUNO_API_KEY not set")
            return MockMusicProvider()
        from app.services.ai.providers.suno_provider import SunoMusicProvider
        return SunoMusicProvider()

    return MockMusicProvider()


def get_video_clip_provider() -> VideoClipProvider:
    from app.services.ai.providers.mock import MockVideoClipProvider

    provider = settings.VIDEO_PROVIDER.lower()
    if provider == "runway":
        if not settings.RUNWAY_API_KEY:
            _warn_fallback("runway", "RUNWAY_API_KEY not set")
            return MockVideoClipProvider()
        from app.services.ai.providers.runway_provider import RunwayVideoProvider
        return RunwayVideoProvider()

    return MockVideoClipProvider()
