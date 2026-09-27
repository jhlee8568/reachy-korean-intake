"""Input isolation, silence rejection, and cancellation behavior."""

import time

import httpx
import numpy as np
import pytest

from reachy_korean_intake.korean_input import KoreanInput


@pytest.mark.asyncio
async def test_silence_and_playback_do_not_create_requests() -> None:
    """Silence and the robot's own playback must not reach the recognizer."""
    received: list[str] = []

    async def submit(text: str) -> None:
        received.append(text)

    capture = KoreanInput("http://127.0.0.1/transcribe", submit)
    silence = np.zeros(1600, dtype=np.int16)
    voice = np.full(1600, 1000, dtype=np.int16)
    capture.play_until = time.monotonic() - 10
    for _ in range(30):
        capture.receive((16000, silence), False)
    assert capture.task is None
    for _ in range(30):
        capture.receive((16000, voice), True)
    assert capture.task is None
    assert not received


@pytest.mark.asyncio
async def test_cancelled_turn_drops_completed_transcription(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stopping or restarting must not inject an old recognition result."""
    received: list[str] = []

    async def submit(text: str) -> None:
        received.append(text)

    capture = KoreanInput("http://127.0.0.1/transcribe", submit)
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"text": "배가 아파요"}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport))
    generation = capture.generation
    capture.reset()
    await capture.transcribe(np.zeros(1600, dtype=np.float32), 16000, generation)
    assert received == []
    await capture.transcribe(np.zeros(1600, dtype=np.float32), 16000, capture.generation)
    assert received == ["배가 아파요"]
