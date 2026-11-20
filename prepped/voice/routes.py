"""HTTP endpoints for the local voice layer."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from prepped.voice.errors import VoiceError
from prepped.voice.service import VoiceService


logger = logging.getLogger(__name__)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1_200)


def create_voice_router(service: VoiceService) -> APIRouter:
    router = APIRouter(prefix="/api/voice", tags=["voice"])

    @router.get("/status")
    def voice_status() -> dict[str, Any]:
        return service.status()

    @router.post("/transcribe")
    async def transcribe_audio(request: Request) -> dict[str, Any]:
        # Reject a declared oversized body before reading it, then enforce the
        # same bound while streaming so a missing/false Content-Length cannot
        # force the whole upload into memory.
        max_bytes = service.settings.max_audio_bytes
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "The recording is too long to transcribe. Keep it under "
                            f"{service.settings.max_recording_seconds} seconds or type your answer."
                        ),
                    )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Content-Length header.")

        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "The recording is too long to transcribe. Keep it under "
                        f"{service.settings.max_recording_seconds} seconds or type your answer."
                    ),
                )
            body.extend(chunk)

        content_type = request.headers.get("content-type", "")
        try:
            return await run_in_threadpool(service.transcribe, bytes(body), content_type)
        except VoiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
        except Exception as exc:  # unexpected engine bug: keep learner on text mode
            logger.error("Unexpected local transcription failure (%s)", type(exc).__name__)
            raise HTTPException(
                status_code=500,
                detail="Local speech-to-text failed unexpectedly. You can type your answer instead.",
            ) from exc

    @router.post("/tts")
    def speak_question(payload: SpeechRequest) -> Response:
        try:
            audio = service.synthesize(payload.text)
        except VoiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
        except Exception as exc:
            logger.error("Unexpected local text-to-speech failure (%s)", type(exc).__name__)
            raise HTTPException(
                status_code=500,
                detail="Local spoken prompts failed unexpectedly. Read the question on screen.",
            ) from exc
        return Response(
            content=audio,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": "inline; filename=question.wav",
            },
        )

    return router
