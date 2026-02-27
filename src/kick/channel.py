# src/kick/channel.py

import requests
from typing import Any, Dict, List, Optional

from .auth import AuthManager
from .exceptions import (
    KickAuthenticationError,
    KickAPIError,
    KickRateLimitError,
)

class ChannelOperations:
    """
    Handles all channel-related operations:
    - Getting current channel info
    - Updating stream title, category, tags
    """

    def __init__(self):
        # No extra init needed — we inherit from AuthManager which has token access
        pass

    def get_channel(self) -> Optional[Dict[str, Any]]:
        """
        Get your own channel info (title, category, tags, slug, etc.)
        Uses no query params first (recommended), falls back if needed.
        """
        token = self.get_access_token(scopes="user:read channel:read channel:write")
        if not token:
            raise KickAuthenticationError("No valid token")


        # Primary attempt: no params (API infers from token)
        print("Requesting own channel: https://api.kick.com/public/v1/channels (no params)")
        r = requests.get(
            "https://api.kick.com/public/v1/channels",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if r.status_code == 200:
            try:
                js = r.json()
                print("Full channel response:", js)  # debug – remove later
                data = js.get("data", [])
                if data:
                    channel = data[0]
                    print(f"✅ Channel found → slug: {channel.get('slug')}")
                    return channel
                else:
                    print("200 but empty data → trying fallback...")
            except Exception as e:
                print("JSON error:", e)

        # Fallback: try with broadcaster_user_id param
        user = self.get_user()  # assumes get_user is available via mixin
        if user and 'user_id' in user:
            broadcaster_id = int(user['user_id'])
            print(f"Fallback: https://api.kick.com/public/v1/channels?broadcaster_user_id={broadcaster_id}")
            r = requests.get(
                f"https://api.kick.com/public/v1/channels?broadcaster_user_id={broadcaster_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

        if r.status_code == 200:
            js = r.json()
            print("Full fallback response:", js)  # debug
            data = js.get("data", [])
            return data[0] if data else None

        if r.status_code == 401:
            raise KickAuthenticationError("Unauthorized – check scopes or re-authenticate")
        raise KickAPIError(r.status_code, r.text)

    def update_channel(
        self,
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        custom_tags: Optional[str | List[str]] = None,
    ) -> Dict[str, Any] | None:
        """
        Update stream title, category, or tags (requires channel:write scope).
        Returns response data or success dict on 200/204, None on failure.
        """
        token = self.get_access_token(scopes="user:read channel:write")
        if not token:
            raise KickAuthenticationError("No valid token")

        body: Dict[str, Any] = {}
        if title is not None:
            body["stream_title"] = title
        if category_id is not None:
            body["category_id"] = int(category_id)
        if custom_tags is not None:
            if isinstance(custom_tags, str):
                custom_tags = [t.strip() for t in custom_tags.split(",") if t.strip()]
            body["custom_tags"] = custom_tags

        if not body:
            raise ValueError("No updates provided")

        r = requests.patch(
            "https://api.kick.com/public/v1/channels",
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        if r.status_code in (200, 204):
            print("✅ Stream updated successfully!")
            return r.json() if r.text else {"success": True}
        if r.status_code == 401:
            raise KickAuthenticationError("Unauthorized – channel:write scope missing?")
        if r.status_code == 429:
            raise KickRateLimitError(retry_after=r.headers.get("Retry-After"))
        raise KickAPIError(r.status_code, r.text)

    def _raw_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Low-level helper for any Kick API request.
        Automatically adds Bearer token.
        """
        token = self.get_access_token()
        if not token:
            raise KickAPIError("No valid access token available")

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        if "json" in kwargs and kwargs["json"] is not None:
            headers["Content-Type"] = "application/json"

        full_url = f"https://api.kick.com{endpoint}"
        return requests.request(method, full_url, headers=headers, **kwargs)