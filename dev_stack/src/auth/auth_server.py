import base64
import hashlib
import os
import webbrowser
from threading import Thread

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

CLIENT_ID = "Qzu2iNFOTNwZ2UiT0xaVsgzS85xW7zcC"
AUTH0_DOMAIN = "driverai-dev.us.auth0.com"
# AUDIENCE = "https://eric-miller-api.ngrok.io/api/v1"

# AUTH0_DOMAIN = "YOUR_DOMAIN.auth0.com"
REDIRECT_URI = "http://localhost:4001/callback"
ORG_ID = "YOUR_ORG_ID"  # Optional

app = FastAPI()
auth_code_container = {}


def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    return verifier, challenge


@app.get("/callback", response_class=HTMLResponse)
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("No code provided", status_code=400)

    auth_code_container["code"] = code
    return "<h2>Login successful. You can close this window.</h2>"


def run_fastapi_server():
    uvicorn.run(app, host="127.0.0.1", port=3000)


def get_tokens(code, verifier):
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = httpx.post(token_url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def login_via_browser():
    verifier, challenge = generate_pkce_pair()

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email offline_access",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "organization": ORG_ID,
    }

    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://{AUTH0_DOMAIN}/authorize?{query}"

    print("Opening browser for Auth0 login...")
    webbrowser.open(url)

    print("Waiting for auth code...")
    while "code" not in auth_code_container:
        pass

    code = auth_code_container["code"]
    print("Auth code received. Exchanging for tokens...")
    tokens = get_tokens(code, verifier)
    return tokens


if __name__ == "__main__":
    thread = Thread(target=run_fastapi_server, daemon=True)
    thread.start()

    tokens = login_via_browser()
    print("Access Token:", tokens.get("access_token"))
    print("ID Token:", tokens.get("id_token"))
