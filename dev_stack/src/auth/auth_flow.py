import base64
import hashlib
import os
import webbrowser
from threading import Thread

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

AUTH0_DOMAIN = "driverai-dev.us.auth0.com"
CLIENT_ID = "Qzu2iNFOTNwZ2UiT0xaVsgzS85xW7zcC"
ORG_ID = "org_s76pU1v8LAYhTOWB"
REDIRECT_URI = "http://localhost:4001/callback"
SCOPES = "openid profile email offline_access"

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
        return HTMLResponse("No code in request", status_code=400)
    auth_code_container["code"] = code
    return "<h3>✅ Login successful. You can close this window.</h3>"


def run_server():
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=4001,
        log_level="critical",  # 🔕 disables info/debug logs
        access_log=False,  # 🔕 disables access logs
    )


def get_tokens(code, verifier):
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = httpx.post(
        f"https://{AUTH0_DOMAIN}/oauth/token", data=payload, headers=headers
    )
    resp.raise_for_status()
    return resp.json()


def login():
    verifier, challenge = generate_pkce_pair()

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        # "state":ORG_ID,
        # "organization": ORG_ID,
    }

    url = f"https://{AUTH0_DOMAIN}/authorize?" + "&".join(
        f"{k}={v}" for k, v in params.items()
    )
    webbrowser.open(url)

    # print("🌐 Waiting for browser login...")

    thread = Thread(target=run_server, daemon=True)
    thread.start()

    while "code" not in auth_code_container:
        pass

    return get_tokens(auth_code_container["code"], verifier)
