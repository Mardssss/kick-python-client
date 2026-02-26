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


class KickClient:
    """
    Reusable Kick.com API client (OAuth2 + PKCE + token refresh + stream management)
    Works with any of your projects – just import and use!
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

        self.access_token = None
        self.refresh_token = None
        self._token_data = None
        self._code_queue: Queue = Queue()
        self._state = None

        self._app = Flask(__name__)

        # Flask callback route (one-time per auth flow)
        @self._app.route("/callback")
        def callback():
            code = request.args.get("code")
            state = request.args.get("state")
            if code and state == self._state:
                self._code_queue.put(code)
                return "<h2>✅ Success! You can close this tab now.</h2>"
            return "<h2>❌ Error: no code or state mismatch</h2>", 400

        self._load_token()

    def _load_token(self):
        """Load saved tokens from file"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    self._token_data = json.load(f)
                self.access_token = self._token_data.get("access_token")
                self.refresh_token = self._token_data.get("refresh_token")
            except Exception:
                pass

    def _save_token(self, token_data: dict):
        """Save tokens to file"""
        self._token_data = token_data
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

    def _test_token(self) -> bool:
        """Quick check if current token still works"""
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
        """Try to refresh using refresh_token"""
        if not self.refresh_token:
            return False
        print("🔄 Refreshing access token...")
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
        print("❌ Refresh failed:", r.text)
        return False

    def _run_flask(self):
        """Start tiny Flask server in background"""
        self._app.run(port=self.flask_port, debug=False, use_reloader=False)

    def _full_oauth_flow(self, scopes: str = "user:read channel:write") -> str | None:
        """Complete browser-based OAuth flow (PKCE)"""
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

        # Start Flask only when we need the callback
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

        print("❌ Token exchange failed:", r.text)
        return None

    def get_access_token(self, scopes: str = "user:read channel:write", force_new: bool = False) -> str | None:
        """Main method – returns a valid access token (auto refresh or full login)"""
        if not force_new and self._test_token():
            return self.access_token

        if not force_new and self.refresh_token and self._refresh_token():
            return self.access_token

        # Full OAuth flow (opens browser once)
        return self._full_oauth_flow(scopes)

    # ====================== API METHODS ======================

    def get_user(self) -> dict | None:
        """Get your own user info (username, user_id, email, etc.)"""
        token = self.get_access_token()
        if not token:
            return None
        r = requests.get(
            "https://api.kick.com/public/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            data = r.json().get("data", [{}])
            return data[0] if data else {}
        print("❌ get_user failed:", r.text)
        return None

    def get_channel(self) -> dict | None:
        """Get your own channel info (title, category, tags, etc.)"""
        # Force channel:read scope for safety
        token = self.get_access_token(scopes="user:read channel:read channel:write")
        if not token:
            return None

        # Try the cleanest way first
        print("Requesting own channel: https://api.kick.com/public/v1/channels (no params)")
        r = requests.get(
            "https://api.kick.com/public/v1/channels",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if r.status_code == 200:
            try:
                js = r.json()
                print("Full channel response:", js)   # ← keep this for now to see everything
                data = js.get("data", [])
                if data:
                    channel = data[0]
                    print(f"✅ Channel found → slug: {channel.get('slug')}")
                    return channel
                else:
                    print("200 but empty data → trying with broadcaster_user_ids param...")
            except Exception as e:
                print("JSON error:", e)

        # Fallback: use plural broadcaster_user_ids (what the official Kick SDK uses)
        user = self.get_user()
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
            print("Full fallback response:", js)
            data = js.get("data", [])
            return data[0] if data else None
        else:
            print(f"❌ get_channel failed: {r.status_code} {r.text}")
            return None

    def update_channel(
        self,
        title: str | None = None,
        category_id: int | None = None,
        custom_tags: str | list[str] | None = None,
    ) -> dict | None:
        """Update stream title, category, or tags (channel:write scope)"""
        token = self.get_access_token(scopes="user:read channel:write")
        if not token:
            return None

        body = {}
        if title is not None:
            body["stream_title"] = title
        if category_id is not None:
            body["category_id"] = int(category_id)
        if custom_tags is not None:
            if isinstance(custom_tags, str):
                custom_tags = [t.strip() for t in custom_tags.split(",") if t.strip()]
            body["custom_tags"] = custom_tags

        if not body:
            print("⚠️ Nothing to update")
            return None

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
        print("❌ Update failed:", r.status_code, r.text)
        return None

    def _raw_request(self, method: str, endpoint: str, **kwargs):
        """Helper for any other endpoint you want to call later"""
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
        return requests.request(method, f"https://api.kick.com{endpoint}", headers=headers, **kwargs)
