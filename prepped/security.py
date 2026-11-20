"""Small ASGI security controls for the local-only Prepped application."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

DEFAULT_API_BODY_LIMIT = 1 * 1024 * 1024
BACKUP_BODY_LIMIT = 25 * 1024 * 1024
VOICE_BODY_LIMIT = 12 * 1024 * 1024


class _RequestBodyTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    """Bound request bodies before FastAPI/Pydantic buffers or parses them."""

    def __init__(self, app: Callable[..., Any]) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope.get("type") != "http" or scope.get("method") not in {"POST", "PUT", "PATCH", "DELETE"}:
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if path == "/api/data/restore":
            limit = BACKUP_BODY_LIMIT
        elif path == "/api/voice/transcribe":
            limit = VOICE_BODY_LIMIT
        elif path.startswith("/api/"):
            limit = DEFAULT_API_BODY_LIMIT
        else:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        declared = headers.get(b"content-length")
        if declared is not None:
            try:
                declared_size = int(declared)
                if declared_size < 0:
                    raise ValueError
            except ValueError:
                await self._reject(send, 400, "Invalid Content-Length header.")
                return
            if declared_size > limit:
                await self._reject(send, 413, "Request body exceeds the local request limit.")
                return

        received = 0
        response_started = False

        async def limited_receive() -> dict[str, Any]:
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise _RequestBodyTooLarge
            return message

        async def tracked_send(message: dict[str, Any]) -> None:
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestBodyTooLarge:
            if response_started:
                raise
            await self._reject(send, 413, "Request body exceeds the local request limit.")

    @staticmethod
    async def _reject(send: Callable[..., Any], status: int, message: str) -> None:
        body = message.encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"cache-control", b"no-store"),
                (b"x-content-type-options", b"nosniff"),
            ],
        })
        await send({"type": "http.response.body", "body": body})
