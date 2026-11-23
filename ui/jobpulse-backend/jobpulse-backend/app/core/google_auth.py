from typing import Any


class GoogleAuthUnavailable(RuntimeError):
    pass


def verify_google_id_token(token: str, audience: str) -> dict[str, Any]:
    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
    except ImportError as exc:
        raise GoogleAuthUnavailable("Install the backend requirements to enable Google sign-in.") from exc

    try:
        return id_token.verify_oauth2_token(token, Request(), audience)
    except GoogleAuthError as exc:
        raise GoogleAuthUnavailable("Google token verification is currently unavailable.") from exc
