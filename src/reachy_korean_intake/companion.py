"""Loopback-only Korean STT; accessed by the robot through an SSH reverse tunnel."""

import os
import asyncio
import logging
from pathlib import Path

import numpy as np
from aiohttp import web
from faster_whisper import WhisperModel


async def serve() -> None:
    """Serve Korean recognition on a loopback socket."""
    model = await asyncio.to_thread(
        WhisperModel,
        "small",
        device="cpu",
        compute_type="int8",
        download_root=os.getenv(
            "REACHY_WHISPER_MODELS", str(Path.home() / ".cache" / "reachy-korean-intake" / "models")
        ),
        local_files_only=False,
    )
    lock = asyncio.Lock()

    def transcribe(raw: bytes) -> str:
        audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
        segments, _ = model.transcribe(
            audio,
            language="ko",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return " ".join(s.text.strip() for s in segments if s.no_speech_prob < 0.6 and s.avg_logprob > -1.0).strip()

    async def recognize(request: web.Request) -> web.Response:
        raw = await request.read()
        if not raw or len(raw) % 2 or len(raw) > 16000 * 2 * 16:
            raise web.HTTPBadRequest(text="Expected up to 16s mono 16kHz PCM16")
        async with lock:
            text = await asyncio.to_thread(transcribe, raw)
        print("한국어 답변 인식 완료" if text else "음성을 확인하지 못했습니다", flush=True)
        return web.json_response({"text": text})

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"ready": True, "language": "ko"})

    app = web.Application(client_max_size=16000 * 2 * 16)
    app.router.add_post("/transcribe", recognize)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", 8766).start()
    print("Korean Whisper ready on localhost:8766; audio is not saved.", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def main() -> None:
    """Run the Korean companion for Reachy Mini."""
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(serve())


if __name__ == "__main__":
    main()
