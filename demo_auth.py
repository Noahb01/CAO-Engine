"""HTTP Basic Auth voor de demo-deploy (wachtwoord via DEMO_WACHTWOORD)."""

import base64
import binascii
import os
import secrets
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "demo")


def demo_wachtwoord() -> Optional[str]:
    wachtwoord = os.environ.get("DEMO_WACHTWOORD", "").strip()
    return wachtwoord or None


def auth_vereist() -> bool:
    return demo_wachtwoord() is not None


class DemoAuthMiddleware(BaseHTTPMiddleware):
    """Blokkeert alle routes zolang DEMO_WACHTWOORD is gezet en auth ontbreekt."""

    async def dispatch(self, request: Request, call_next):
        wachtwoord = demo_wachtwoord()
        if wachtwoord is None:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return _unauthorized()

        try:
            decoded = base64.b64decode(auth_header[6:].encode("ascii")).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return _unauthorized()

        username, sep, password = decoded.partition(":")
        if not sep:
            return _unauthorized()

        ok = secrets.compare_digest(username, DEMO_USERNAME) and secrets.compare_digest(
            password, wachtwoord
        )
        if not ok:
            return _unauthorized()

        return await call_next(request)


def _unauthorized() -> Response:
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Inschaling demo"'},
        content="Authenticatie vereist voor deze demo.",
        media_type="text/plain; charset=utf-8",
    )
