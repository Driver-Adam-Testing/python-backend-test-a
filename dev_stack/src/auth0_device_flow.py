import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx


class Auth0DeviceAuthenticator:
    def __init__(
        self,
        client_id,
        domain,
        audience=None,
        scope="openid profile email offline_access",
        cache_file=None,
    ):
        self.client_id = client_id
        self.domain = domain
        self.audience = audience
        self.scope = scope
        self.device_code_url = f"https://{self.domain}/oauth/device/code"
        self.token_url = f"https://{self.domain}/oauth/token"
        self.cache_file = cache_file or Path.home() / ".mycli_tokens.json"

    def authenticate(self):
        tokens = self._load_cached_tokens()
        if tokens:
            if not self._is_token_expired(tokens):
                return tokens
            elif "refresh_token" in tokens:
                refreshed = self._refresh_token(tokens["refresh_token"])
                if refreshed:
                    self._cache_tokens(refreshed)
                    return refreshed

        print("Starting Auth0 Device Authorization Flow...")

        device_payload = {
            "client_id": self.client_id,
            "scope": self.scope,
        }
        if self.audience:
            device_payload["audience"] = self.audience

        with httpx.Client() as client:
            response = client.post(
                self.device_code_url,
                data=device_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

        print("\n== Log in to continue ==")
        print(f"Visit: {data['verification_uri_complete']}")
        print(f"Or: {data['verification_uri']} and enter code: {data['user_code']}\n")

        tokens = self._poll_for_token(data)
        self._cache_tokens(tokens)
        return tokens

    def _poll_for_token(self, device_data):
        interval = device_data.get("interval", 5)
        expires_at = datetime.utcnow() + timedelta(
            seconds=device_data.get("expires_in", 900)
        )

        while datetime.utcnow() < expires_at:
            time.sleep(interval)
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_data["device_code"],
                "client_id": self.client_id,
            }

            with httpx.Client() as client:
                print(payload)
                resp = client.post(
                    self.token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            if resp.status_code == 200:
                return self._add_expiration(resp.json())
            elif resp.status_code == 400:
                error = resp.json().get("error")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                elif error == "expired_token":
                    raise Exception("⏱️ Device code expired. Please try again.")
                elif error == "access_denied":
                    raise Exception(
                        "🚫 Access was denied. User may have declined authorization."
                    )
                else:
                    raise Exception(f"Authentication failed: {error}")
            else:
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    print(f"HTTP error occurred: {e}")
                    raise

        raise TimeoutError("⏳ Login timed out. Please start the login flow again.")

        interval = device_data.get("interval", 60)
        while True:
            time.sleep(interval)
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_data["device_code"],
                "client_id": self.client_id,
            }

            with httpx.Client() as client:
                resp = client.post(self.token_url, data=payload)

            if resp.status_code == 200:
                return self._add_expiration(resp.json())
            elif resp.status_code == 400:
                error = resp.json().get("error")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                else:
                    raise Exception(f"Authentication failed: {error}")
            else:
                resp.raise_for_status()

    def _refresh_token(self, refresh_token):
        try:
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token,
            }
            with httpx.Client() as client:
                resp = client.post(self.token_url, data=payload)
            if resp.status_code == 200:
                print("🔁 Access token refreshed.")
                return self._add_expiration(resp.json(), fallback=refresh_token)
            else:
                print("⚠️ Refresh token invalid or expired.")
                self.clear_cache()
                return None
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return None

    def _add_expiration(self, tokens, fallback=None):
        if "expires_in" in tokens:
            expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
            tokens["expires_at"] = expires_at.isoformat()
        elif fallback:
            tokens["refresh_token"] = fallback
        return tokens

    def _is_token_expired(self, tokens):
        try:
            expires_at = datetime.fromisoformat(tokens["expires_at"])
            return datetime.utcnow() >= expires_at
        except Exception:
            return True

    def _load_cached_tokens(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file) as f:
                return json.load(f)
        return None

    def _cache_tokens(self, tokens):
        with open(self.cache_file, "w") as f:
            json.dump(tokens, f)

    def clear_cache(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print("🔓 Auth token cache cleared.")
