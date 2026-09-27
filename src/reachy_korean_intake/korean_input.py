"""Korean-only microphone recognition through the local companion."""

import time
import asyncio
import logging
from collections import deque
from collections.abc import Callable, Awaitable

import httpx
import numpy as np
from numpy.typing import NDArray

from reachy_korean_intake.conversation_handler import AudioFrame


logger = logging.getLogger(__name__)


class KoreanInput:
    """Segment speech and deliver Korean transcripts without blocking capture."""

    def __init__(self, url: str, submit: Callable[[str], Awaitable[None]]) -> None:
        """Bind the local endpoint and transcript receiver."""
        self.url = url
        self.submit = submit
        self.error = ""
        self.ready = False
        self.play_until = time.monotonic() + 2
        self.task: asyncio.Task[None] | None = None
        self.generation = 0
        self.pre: deque[NDArray[np.float32]] = deque(maxlen=5)
        self.frames: list[NDArray[np.float32]] = []
        self.duration = self.silence = self.voiced = 0.0

    def reset(self) -> None:
        """Discard captured audio and invalidate recognition in flight."""
        self.generation += 1
        self.pre.clear()
        self.frames.clear()
        self.duration = self.silence = self.voiced = 0.0

    async def health(self) -> bool:
        """Check the companion without sending microphone audio."""
        try:
            async with httpx.AsyncClient(timeout=2, trust_env=False) as client:
                response = await client.get(self.url.rsplit("/", 1)[0] + "/health")
                response.raise_for_status()
                self.ready = response.json().get("language") == "ko"
            self.error = "" if self.ready else "한국어 인식 도우미를 확인해 주세요."
        except (httpx.HTTPError, ValueError) as exc:
            if self.ready:
                logger.warning("Korean companion disconnected: %s", type(exc).__name__)
            self.ready = False
            self.error = "Mac에서 한국어 인식 도우미를 실행해 주세요."
        return self.ready

    def receive(self, frame: AudioFrame, blocked: bool) -> None:
        """Collect one utterance while the robot is listening."""
        if blocked or time.monotonic() < self.play_until + 0.5 or (self.task and not self.task.done()):
            self.pre.clear()
            self.frames.clear()
            self.duration = self.silence = self.voiced = 0.0
            return
        rate, audio = frame
        if not audio.size or rate <= 0:
            return
        if audio.ndim == 2:
            if audio.shape[1] > audio.shape[0]:
                audio = audio.T
            audio = audio[:, 0]
        samples = audio.astype(np.float32)
        if audio.dtype == np.int16:
            samples /= np.float32(32768)
        seconds = len(samples) / rate
        speaking = float(np.sqrt(np.mean(samples * samples))) >= 0.006
        if not self.frames:
            if not speaking:
                self.pre.append(samples.copy())
                return
            self.frames = list(self.pre)
            self.pre.clear()
        self.frames.append(samples.copy())
        self.duration += seconds
        self.voiced += seconds if speaking else 0
        self.silence = 0 if speaking else self.silence + seconds
        if self.silence < 0.9 and self.duration < 12:
            return
        utterance = np.concatenate(self.frames) if self.voiced >= 0.2 else None
        self.reset()
        if utterance is not None:
            self.task = asyncio.create_task(self.transcribe(utterance, rate, self.generation))

    async def transcribe(self, audio: NDArray[np.float32], rate: int, generation: int) -> None:
        """Send audio to the companion and ignore results from cancelled turns."""
        if rate != 16000:
            audio = np.interp(
                np.arange(round(len(audio) * 16000 / rate)) * rate / 16000, np.arange(len(audio)), audio
            ).astype(np.float32)
        raw = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        try:
            async with httpx.AsyncClient(timeout=25, trust_env=False) as client:
                response = await client.post(
                    self.url, content=raw, headers={"Content-Type": "application/octet-stream"}
                )
                response.raise_for_status()
                text = str(response.json()["text"]).strip()
            self.ready, self.error = True, ""
            if generation == self.generation:
                await self.submit(text)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("Korean recognition unavailable: %s", type(exc).__name__)
            self.ready = False
            self.error = "인식 연결이 끊겼어요. Mac 도우미를 확인하고 다시 시작해 주세요."
        except Exception:
            logger.exception("Failed to deliver Korean transcript")
            self.error = "답변을 전달하지 못했어요. 다시 시작해 주세요."
