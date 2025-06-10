import json

import auth_flow
import click
import httpx
from token_store import clear_tokens, load_tokens, save_tokens


@click.group()
def cli():
    """🔐 Auth CLI using FastAPI + Auth0 PKCE"""


@cli.command()
def login():
    """🔑 Login to Auth0"""
    tokens = auth_flow.login()
    save_tokens(tokens)
    click.echo("✅ Login successful. Tokens cached.")


@cli.command()
def whoami():
    """👤 Fetch current user profile from Auth0"""
    tokens = load_tokens()
    if not tokens:
        click.echo("❌ Not logged in. Run `login`.")
        return

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = httpx.get(f"https://{auth_flow.AUTH0_DOMAIN}/userinfo", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        click.echo("👤 " + json.dumps(data, indent=2))
    else:
        click.echo("⚠️ Could not fetch user info. Try `login` again.")


@cli.command()
def logout():
    """🚪 Log out and remove tokens"""
    clear_tokens()
    click.echo("👋 Logged out.")


if __name__ == "__main__":
    cli()
