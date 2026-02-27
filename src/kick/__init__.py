# src/kick/__init__.py

from .client import KickClient
from .exceptions import (
    KickError,
    KickAuthenticationError,
    KickAPIError,
    KickRateLimitError,
    KickTokenExpiredError,
)

__version__ = "1.1.0"
__author__ = "Mardssss"
__license__ = "MIT"          

__all__ = [
    "KickClient",
    "KickError",
    "KickAuthenticationError",
    "KickAPIError",
    "KickRateLimitError",
    "KickTokenExpiredError",
]