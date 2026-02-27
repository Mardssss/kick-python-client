# src/kick/user.py

import requests
from typing import Any, Dict, Optional

from .auth import AuthManager
from .exceptions import (
    KickAuthenticationError,
    KickAPIError,
)
class UserOperations:
    """
    Handles user-related API operations.
    Currently: only fetching the authenticated user's own information.
    """

    def __init__(self):
        # No extra initialization needed — inherits token access from AuthManager
        pass

    def get_user(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve information about the currently authenticated user.

        Returns:
            dict | None: User data (name, user_id, profile_picture, etc.) or None on failure
        """
        token = self.get_access_token(scopes="user:read")
        if not token:
            raise KickAuthenticationError("No valid token available for user request")

        r = requests.get(
            "https://api.kick.com/public/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if r.status_code == 200:
            data = r.json().get("data", [{}])
            return data[0] if data else None
        
        if r.status_code == 401:
            raise KickAuthenticationError("Unauthorized – token invalid or scopes missing")
        raise KickAPIError(r.status_code, r.text)