"""Factory functions that return the configured AI provider based on env vars."""
from app.core.config import settings
from app.services.ai.base import LLMProvider, ImageProvider, TTSProvider, MusicProvider, VideoClipProvider


def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "openai":
        from app.services.ai.providers.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider()
    if settings.LLM_PROVIDER == "anthropic":
        from app.services.ai.providers.anthropic_provider import AnthropicLLMProvider
        return AnthropicLLMProvider()
    from app.services.ai.providers.mock import MockLLMProvider
    return MockLLMProvider()


def get_image_provider() -> ImageProvider:
    if settings.IMAGE_PROVIDER == "openai":
        from app.services.ai.providers.openai_provider import OpenAIImageProvider
        return OpenAIImageProvider()
    from app.services.ai.providers.mock import MockImageProvider
    return MockImageProvider()


def get_tts_provider() -> TTSProvider:
    if settings.TTS_PROVIDER == "elevenlabs":
        from app.services.ai.providers.elevenlabs_provider import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider()
    from app.services.ai.providers.mock import MockTTSProvider
    return MockTTSProvider()


def get_music_provider() -> MusicProvider:
    from app.services.ai.providers.mock import MockMusicProvider
    return MockMusicProvider()


def get_video_clip_provider() -> VideoClipProvider:
    from app.services.ai.providers.mock import MockVideoClipProvider
    return MockVideoClipProvider()
