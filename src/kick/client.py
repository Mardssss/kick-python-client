# src/kick/client.py
import requests
from typing import Any, Dict, List, Optional

from .auth import AuthManager
from .channel import ChannelOperations
from .user import UserOperations

class KickClient(AuthManager, UserOperations, ChannelOperations):
    """
    Main entry point to the Kick.com API client.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
        token_file: str = "kick_tokens.json",
        flask_port: int = 8080,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_file=token_file,
            flask_port=flask_port,
        )
