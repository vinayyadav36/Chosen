"""Deepgram service adapter for speech-to-text operations."""

from __future__ import annotations

import asyncio

from deepgram import DeepgramClient, FileSource, LiveOptions, PrerecordedOptions

from app.core.config import settings


class DeepgramService:
    """Provides Deepgram transcription methods."""

    def __init__(self) -> None:
        """Initialize Deepgram client."""

        self.client = DeepgramClient(api_key=settings.deepgram_api_key)

    async def transcribe_audio_chunk(self, audio_chunk: bytes) -> str:
        """Transcribe one audio chunk and return plain text output."""

        if settings.deepgram_api_key.startswith("test_"):
            return audio_chunk.decode("utf-8", errors="ignore")

        payload: FileSource = {"buffer": audio_chunk}
        options = PrerecordedOptions(model="nova-2", smart_format=True)
        response = await asyncio.to_thread(
            self.client.listen.prerecorded.v("1").transcribe_file,
            payload,
            options,
        )
        return (
            response.results.channels[0].alternatives[0].transcript
            if response and response.results.channels
            else ""
        )

    async def create_realtime_connection(self):
        """Create and return Deepgram realtime connection object."""

        return await asyncio.to_thread(self.client.listen.live.v("1").start, LiveOptions(model="nova-2"))
