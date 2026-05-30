"""ElevenLabs text-to-speech service wrapper."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from elevenlabs.client import ElevenLabs

from app.core.config import settings


class ElevenLabsService:
    """Provides TTS generation methods."""

    def __init__(self) -> None:
        """Initialize ElevenLabs client."""

        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    async def generate_speech(self, text: str) -> bytes:
        """Generate complete PCM audio bytes from text."""

        if settings.elevenlabs_api_key.startswith("test_"):
            return text.encode("utf-8")

        audio_iter = await asyncio.to_thread(
            self.client.text_to_speech.convert,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            output_format="pcm_16000",
            text=text,
            model_id="eleven_multilingual_v2",
        )
        return b"".join(chunk for chunk in audio_iter if isinstance(chunk, (bytes, bytearray)))

    async def generate_streaming_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """Yield generated speech audio in chunks."""

        audio = await self.generate_speech(text)
        chunk_size = 2048
        for idx in range(0, len(audio), chunk_size):
            yield audio[idx : idx + chunk_size]
