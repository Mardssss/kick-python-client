# src/kick/chat.py

import requests
from typing import Optional

from .auth import AuthManager
from .exceptions import KickAPIError, KickAuthenticationError, KickRateLimitError

class ChatOperations:
    """
    Handles chat-related operations: sending messages, moderation (timeout, ban, delete).
    Requires 'chat:write' scope for most methods.
    """

    def __init__(self):
        # No extra init needed — token access inherited from AuthManager
        pass

    def send_chat_message(self, channel_slug: str, message: str) -> bool:
        """
        Send a message to the specified channel's chat.

        Args:
            channel_slug: The channel's slug/username (e.g. "xqc")
            message: The text to send (max length usually ~500 chars)

        Returns:
            bool: True if sent successfully

        Raises:
            KickAuthenticationError: No valid token or missing scope
            KickAPIError: API error (rate limit, invalid message, etc.)
        """
        token = self.get_access_token(scopes="chat:write")
        if not token:
            raise KickAuthenticationError("No valid token for chat:write")

        payload = {"content": message}

        r = requests.post(
            f"https://api.kick.com/public/v1/channels/{channel_slug}/messages",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if r.status_code in (200, 204):
            return True

        if r.status_code == 401:
            raise KickAuthenticationError("Unauthorized – check chat:write scope")
        if r.status_code == 429:
            raise KickRateLimitError(retry_after=r.headers.get("Retry-After"))
        raise KickAPIError(r.status_code, r.text)

    def timeout_user(
        self,
        channel_slug: str,
        user_id: str,
        duration_seconds: int = 600,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Timeout (temporarily ban) a user from the channel's chat.

        Args:
            channel_slug: Channel slug/username
            user_id: Numeric user ID to timeout
            duration_seconds: Ban duration (default 600 = 10 min)
            reason: Optional reason (shown to mods)

        Returns:
            bool: True if successful
        """
        token = self.get_access_token(scopes="chat:write")
        if not token:
            raise KickAuthenticationError("No valid token for chat:write")

        payload = {
            "user_id": user_id,
            "duration": duration_seconds,
        }
        if reason:
            payload["reason"] = reason

        r = requests.post(
            f"https://api.kick.com/public/v1/channels/{channel_slug}/timeouts",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if r.status_code in (200, 204):
            return True

        raise KickAPIError(r.status_code, r.text)

    def ban_user(
        self,
        channel_slug: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Permanently ban a user from the channel's chat.

        Args:
            channel_slug: Channel slug/username
            user_id: Numeric user ID to ban
            reason: Optional reason

        Returns:
            bool: True if successful
        """
        token = self.get_access_token(scopes="chat:write")
        if not token:
            raise KickAuthenticationError("No valid token for chat:write")

        payload = {"user_id": user_id}
        if reason:
            payload["reason"] = reason

        r = requests.post(
            f"https://api.kick.com/public/v1/channels/{channel_slug}/bans",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if r.status_code in (200, 204):
            return True

        raise KickAPIError(r.status_code, r.text)

    def delete_message(
        self,
        channel_slug: str,
        message_id: str,
    ) -> bool:
        """
        Delete a specific message from the channel's chat.

        Args:
            channel_slug: Channel slug/username
            message_id: The ID of the message to delete

        Returns:
            bool: True if deleted
        """
        token = self.get_access_token(scopes="chat:write")
        if not token:
            raise KickAuthenticationError("No valid token for chat:write")

        r = requests.delete(
            f"https://api.kick.com/public/v1/channels/{channel_slug}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if r.status_code in (200, 204):
            return True

        raise KickAPIError(r.status_code, r.text)