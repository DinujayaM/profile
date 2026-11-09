from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class ImageResponse:
    url: str
    provider: str
    model: str
    cost_usd: float
    width: int
    height: int
    revised_prompt: Optional[str] = None


@dataclass
class TTSResponse:
    audio_url: str
    duration_seconds: float
    provider: str
    voice_id: str
    cost_usd: float
    file_key: Optional[str] = None


@dataclass
class MusicResponse:
    audio_url: str
    duration_seconds: float
    provider: str
    title: str
    cost_usd: float
    file_key: Optional[str] = None


@dataclass
class VideoClipResponse:
    video_url: str
    duration_seconds: float
    provider: str
    cost_usd: float
    file_key: Optional[str] = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> LLMResponse:
        pass


class ImageProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, width: int = 1920, height: int = 1080) -> ImageResponse:
        pass


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, language: str = "en-US") -> TTSResponse:
        pass


class MusicProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, duration_seconds: int = 30, lyrics: str = "") -> MusicResponse:
        pass


class VideoClipProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, source_image_url: str, duration_seconds: int = 5) -> VideoClipResponse:
        pass
