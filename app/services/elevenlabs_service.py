"""ElevenLabs TTS service wrapper."""

from __future__ import annotations

import asyncio

from elevenlabs.client import ElevenLabs


class ElevenLabsService:
    """Encapsulates ElevenLabs speech synthesis."""

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key
        self._client = ElevenLabs(api_key=api_key) if api_key else None

    async def generate_speech(self, text: str) -> bytes:
        """Generate speech bytes from text."""

        if not self._client:
            return text.encode("utf-8")
        try:
            iterator = await asyncio.to_thread(
                self._client.text_to_speech.convert,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_multilingual_v2",
            )
            return b"".join(chunk for chunk in iterator if isinstance(chunk, (bytes, bytearray)))
        except Exception:
            return b""
