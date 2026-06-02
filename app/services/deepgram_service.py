"""Deepgram STT service wrapper."""

from __future__ import annotations

import asyncio

from deepgram import DeepgramClient, FileSource, PrerecordedOptions


class DeepgramService:
    """Encapsulates Deepgram transcription operations."""

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key
        self._client = DeepgramClient(api_key=api_key) if api_key else None

    async def transcribe_audio_chunk(self, audio_chunk: bytes) -> str:
        """Transcribe audio bytes and return text."""

        if not self._client:
            return ""
        payload: FileSource = {"buffer": audio_chunk}
        options = PrerecordedOptions(model="nova-2", smart_format=True)
        try:
            response = await asyncio.to_thread(
                self._client.listen.prerecorded.v("1").transcribe_file,
                payload,
                options,
            )
            return response.results.channels[0].alternatives[0].transcript or ""
        except Exception:
            return ""
