# src/kick/chat.py

from typing import Optional

from .auth import AuthManager
from .exceptions import KickAPIError, KickAuthenticationError

class ChatOperations:
    """
    Handles chat-related operations (sending messages, moderation, etc.).
    Currently only a skeleton — functionality to be implemented later.
    Requires 'chat:write' scope for sending messages.
    """

    def __init__(self):
        # No extra init needed — token access inherited
        pass

    def send_chat_message(self, channel_slug: str, message: str) -> bool:
        """
        Send a message to the specified channel's chat.
        """
        raise NotImplementedError(
            "Chat sending not yet implemented. "
            "Requires POST /public/v1/channels/{slug}/messages or similar endpoint."
        )

    def timeout_user(
        self,
        channel_slug: str,
        user_id: str,
        duration_seconds: int = 600,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Timeout (temporarily ban) a user from chat.
        """
        raise NotImplementedError("Timeout/moderation not yet implemented.")

    def ban_user(
        self,
        channel_slug: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Permanent ban from chat."""
        raise NotImplementedError("Ban not yet implemented.")

    def delete_message(
        self,
        channel_slug: str,
        message_id: str,
    ) -> bool:
        """Delete a specific chat message."""
        raise NotImplementedError("Message deletion not yet implemented.")

    # Add more as needed in the future
    # def get_chat_settings(self, channel_slug: str) -> dict:
    #     ...