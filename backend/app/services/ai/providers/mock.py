"""
Mock AI providers for development and testing.
These return realistic-looking responses without calling external APIs.
To use real providers, set the appropriate environment variables.
"""
import asyncio
import json
from app.services.ai.base import (
    LLMProvider, LLMResponse,
    ImageProvider, ImageResponse,
    TTSProvider, TTSResponse,
    MusicProvider, MusicResponse,
    VideoClipProvider, VideoClipResponse,
)

MOCK_SCRIPT_TEMPLATE = """
# {title}

## Introduction
Welcome to TinyTales World! Today we're going on an adventure to learn about {topic}.
Our friend Sunny the sunflower will guide us!

## Main Story
Sunny woke up one morning and wanted to share something special...
[Scene continues with educational content about {topic}]

## Song
🎵 Let's learn about {topic} today,
In the most wonderful and special way!
Count and sing and clap along,
TinyTales World's favourite song! 🎵

## Ending
Great job everyone! Today we learned all about {topic}.
Remember to practice at home. See you next time on TinyTales World!
"""


class MockLLMProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> LLMResponse:
        await asyncio.sleep(0.5)
        topic = "learning"
        for word in ["alphabet", "numbers", "animals", "colors", "shapes"]:
            if word in prompt.lower():
                topic = word
                break
        content = MOCK_SCRIPT_TEMPLATE.format(title="TinyTales Adventure", topic=topic)
        if "ideas" in prompt.lower():
            content = json.dumps([
                {"title": "The ABC Garden", "concept": "Sunny the flower teaches letters", "category": "alphabet"},
                {"title": "Count with Cubby Bear", "concept": "Cubby Bear counts forest friends", "category": "numbers"},
                {"title": "Rainbow Colors Dance", "concept": "Rainbow fairies teach colors", "category": "colors"},
            ])
        return LLMResponse(
            content=content,
            model="mock-gpt-4o",
            provider="mock",
            input_tokens=len(prompt) // 4,
            output_tokens=len(content) // 4,
            cost_usd=0.0,
        )


class MockImageProvider(ImageProvider):
    async def generate(self, prompt: str, width: int = 1920, height: int = 1080) -> ImageResponse:
        await asyncio.sleep(0.3)
        return ImageResponse(
            url="https://placehold.co/1920x1080/FFB347/FFFFFF?text=TinyTales+Scene",
            provider="mock",
            model="mock-dall-e-3",
            cost_usd=0.0,
            width=width,
            height=height,
            revised_prompt=f"[MOCK] {prompt[:100]}",
        )


class MockTTSProvider(TTSProvider):
    async def synthesize(self, text: str, voice_id: str = "sunny", language: str = "en-US") -> TTSResponse:
        await asyncio.sleep(0.2)
        return TTSResponse(
            audio_url="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
            duration_seconds=len(text) / 15,
            provider="mock",
            voice_id=voice_id,
            cost_usd=0.0,
        )


class MockMusicProvider(MusicProvider):
    async def generate(self, prompt: str, duration_seconds: int = 30, lyrics: str = "") -> MusicResponse:
        await asyncio.sleep(0.4)
        return MusicResponse(
            audio_url="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
            duration_seconds=float(duration_seconds),
            provider="mock",
            title="TinyTales Theme",
            cost_usd=0.0,
        )


class MockVideoClipProvider(VideoClipProvider):
    async def generate(self, prompt: str, source_image_url: str, duration_seconds: int = 5) -> VideoClipResponse:
        await asyncio.sleep(1.0)
        return VideoClipResponse(
            video_url="https://www.w3schools.com/html/mov_bbb.mp4",
            duration_seconds=float(duration_seconds),
            provider="mock",
            cost_usd=0.0,
        )
