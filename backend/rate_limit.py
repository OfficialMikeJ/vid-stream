"""Per-IP rate limiting using slowapi (in-memory token bucket).

Limits are intentionally conservative: tighter on auth endpoints to slow
brute-force attacks, looser on read/streaming endpoints. The PlayLab API-key
endpoints are exempted because they're machine-to-machine.
"""
import os
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def client_key(request: Request) -> str:
    """Identify the caller for rate limiting.

    Behind a proxy/load-balancer (e.g. Kubernetes ingress) the request.client
    address is the proxy's internal IP. We honour the standard
    X-Forwarded-For header (first hop = original caller) when present.
    """
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


# Single shared limiter — process-local state. Sufficient for a single-pod
# deployment; for multi-pod, swap `storage_uri` for redis://...
limiter = Limiter(
    key_func=client_key,
    storage_uri=os.environ.get("RATE_LIMIT_STORAGE", "memory://"),
    default_limits=[],  # No global default — apply explicitly per route
    headers_enabled=False,
)


# Named limit groups — referenced from individual routes
LIMIT_LOGIN = "10/minute"          # auth /login — slow brute-force
LIMIT_PASSWORD = "5/minute"        # change-password
LIMIT_UPLOAD_INIT = "30/minute"    # init upload session
LIMIT_COMMENT = "30/minute"        # post comment / caption upload
LIMIT_SHARE_RESOLVE = "120/minute" # public /api/share/{token} resolution


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Return a JSON 429 with retry hint."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down and try again shortly.",
            "limit": str(exc.detail) if hasattr(exc, "detail") else None,
        },
        headers={"Retry-After": "60"},
    )
