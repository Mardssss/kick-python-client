# src/kick/auth.py
import os
import json
import secrets
import hashlib
import base64
import webbrowser
import threading
import time
from queue import Queue, Empty
from flask import Flask, request
import requests
from .exceptions import KickAuthenticationError


class AuthManager:
    """
    Handles all OAuth2 + PKCE authentication logic for Kick.com.
    Manages token loading, refreshing, and browser-based login flow.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
        token_file: str = "kick_tokens.json",
        flask_port: int = 8080,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file
        self.flask_port = flask_port

        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._token_data: dict | None = None
        self._code_queue: Queue = Queue()
        self._state: str | None = None

        self._app = Flask(__name__)

        @self._app.route("/callback")
        def callback():
            code = request.args.get("code")
            state = request.args.get("state")
            if code and state == self._state:
                self._code_queue.put(code)
                return "<h2>✅ Success! You can close this tab now.</h2>"
            return "<h2>❌ Error: no code or state mismatch</h2>", 400

        self._load_token()

    def _load_token(self) -> None:
        """Load saved tokens from file if exists."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    self._token_data = json.load(f)
                self.access_token = self._token_data.get("access_token")
                self.refresh_token = self._token_data.get("refresh_token")
            except Exception:
                pass  # silent fail – we'll re-auth if needed

    def _save_token(self, token_data: dict) -> None:
        """Save tokens to file and update instance variables."""
        self._token_data = token_data
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

    def _test_token(self) -> bool:
        """Quick check if current access token is still valid."""
        if not self.access_token:
            return False
        try:
            r = requests.get(
                "https://api.kick.com/public/v1/users",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10,
            )
            return r.status_code == 200
        except:
            return False

    def _refresh_token(self) -> bool:
        if not self.refresh_token:
            raise KickAuthenticationError("No refresh token available")

        print("🔄 Refreshing access token...")  # keep this for visibility during dev
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        r = requests.post("https://id.kick.com/oauth/token", data=payload)
        if r.status_code == 200:
            self._save_token(r.json())
            print("✅ Token refreshed")
            return True

        raise KickAuthenticationError(f"Refresh failed: {r.status_code} {r.text}")

    def _run_flask(self) -> None:
        """Start tiny Flask server in background for OAuth callback."""
        self._app.run(port=self.flask_port, debug=False, use_reloader=False)

    def _full_oauth_flow(self, scopes: str = "user:read channel:write") -> str | None:
        """Perform complete browser-based OAuth flow with PKCE."""
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("utf-8")).digest()
            )
            .decode("utf-8")
            .rstrip("=")
        )
        self._state = secrets.token_urlsafe(16)

        auth_url = (
            f"https://id.kick.com/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            "response_type=code&"
            f"scope={scopes}&"
            f"state={self._state}&"
            f"code_challenge={code_challenge}&"
            "code_challenge_method=S256"
        )

        print("\n" + "=" * 80)
        print("🔑 Opening Kick login in browser...")
        print("If it doesn't open automatically, copy this URL:")
        print(auth_url)
        print("=" * 80 + "\n")

        webbrowser.open(auth_url)

        # Start Flask in background
        threading.Thread(target=self._run_flask, daemon=True).start()

        print("⏳ Waiting for you to authorize (5 min timeout)...")
        try:
            code = self._code_queue.get(timeout=300)
        except Empty:
            print("❌ Timeout – no authorization code received.")
            return None

        print("✅ Code received, exchanging for token...")

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        }

        r = requests.post("https://id.kick.com/oauth/token", data=payload)

        if r.status_code == 200:
            data = r.json()
            self._save_token(data)
            print("🎉 Tokens saved successfully!")
            return data["access_token"]

        raise KickAuthenticationError(f"Token exchange failed: {r.status_code} {r.text}")


    def get_access_token(self, scopes: str = "user:read channel:write", force_new: bool = False) -> str:
        """
        Returns a valid access token or raises exception if impossible without user interaction.
        """
        # Case 1: existing token works → return it
        if not force_new and self._test_token():
            return self.access_token

        # Case 2: we can refresh → do it
        if not force_new and self.refresh_token and self._refresh_token():
            return self.access_token

        # Case 3: no token + no refresh possible + not forcing new flow → fail fast
        if not force_new:
            if self.access_token is None and self.refresh_token is None:
                raise KickAuthenticationError(
                    "No valid access token and no refresh token available. "
                    "Call with force_new=True or re-authenticate manually."
                )
            # If we reach here, something inconsistent happened
            raise KickAuthenticationError("Token state invalid – cannot proceed without user interaction")

        # Case 4: force_new=True → start browser flow
        token = self._full_oauth_flow(scopes)
        if token is None:
            raise KickAuthenticationError("Full OAuth flow failed (timeout or error)")
        return token
