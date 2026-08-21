"""
FastAPI middleware for the Medical RAG API.

Middleware stack (applied in order):
  1. RequestIDMiddleware  — inject X-Request-ID header
  2. RateLimitMiddleware  — token-bucket per client IP (in-memory)
  3. SecurityHeadersMiddleware — add OWASP security headers

Privacy: middleware logs only request hashes and IDs, never raw content.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique X-Request-ID into every request/response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory token-bucket rate limiter per client IP.

    Defaults: 60 requests / 60 seconds per IP.
    Exempt paths: /health, /docs, /openapi.json.
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
    DEFAULT_LIMIT = 60
    DEFAULT_WINDOW = 60  # seconds

    def __init__(
        self,
        app,  # type: ignore[no-untyped-def]
        limit: int = DEFAULT_LIMIT,
        window: int = DEFAULT_WINDOW,
    ) -> None:
        super().__init__(app)
        self._limit = limit
        self._window = window
        # {ip: (count, window_start)}
        self._buckets: dict[str, tuple[int, float]] = defaultdict(
            lambda: (0, time.monotonic())
        )

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.monotonic()
        count, window_start = self._buckets[ip]

        if now - window_start > self._window:
            # New window
            self._buckets[ip] = (1, now)
        elif count >= self._limit:
            log.warning("Rate limit exceeded for IP %s", ip)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Max {self._limit} requests per {self._window}s.",
                },
                headers={"Retry-After": str(self._window)},
            )
        else:
            self._buckets[ip] = (count + 1, window_start)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        return response
