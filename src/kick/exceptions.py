# src/kick/exceptions.py

class KickError(Exception):
    """Base exception for all Kick API client errors."""
    pass


class KickAuthenticationError(KickError):
    """
    Raised when authentication fails (invalid token, refresh failed, timeout, etc.).
    """
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class KickAPIError(KickError):
    """
    Raised when the Kick API returns an error status code or invalid response.
    """
    def __init__(self, status_code: int, message: str = "API request failed"):
        self.status_code = status_code
        self.message = f"API error {status_code}: {message}"
        super().__init__(self.message)


class KickRateLimitError(KickAPIError):
    """Specific case for rate limiting (429)."""
    def __init__(self, retry_after: int | None = None):
        msg = "Rate limited by Kick API"
        if retry_after is not None:
            msg += f" — retry after {retry_after} seconds"
        super().__init__(429, msg)


class KickTokenExpiredError(KickAuthenticationError):
    """Raised when token is expired and cannot be refreshed."""
    def __init__(self):
        super().__init__("Access token expired and refresh failed")

"""
Usage example
if r.status_code == 401:
    raise KickAuthenticationError("Unauthorized – check scopes or re-authenticate")
if r.status_code == 429:
    raise KickRateLimitError(retry_after=r.headers.get("Retry-After"))
"""