import click
import httpx
from auth0_device_flow import Auth0DeviceAuthenticator

CLIENT_ID = "Qzu2iNFOTNwZ2UiT0xaVsgzS85xW7zcC"
DOMAIN = "driverai-dev.us.auth0.com"
# AUDIENCE = "https://eric-miller-api.ngrok.io/api/v1"

auth = Auth0DeviceAuthenticator(client_id=CLIENT_ID, domain=DOMAIN)


# https://auth0.com/docs/quickstart/native/device#request-device-code
@click.group()
def cli():
    pass


@cli.command()
def login():
    tokens = auth.authenticate()
    click.echo("✅ Logged in successfully.")


@cli.command()
def whoami():
    tokens = auth.authenticate()
    access_token = tokens["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    userinfo_url = f"https://{DOMAIN}/userinfo"

    with httpx.Client() as client:
        resp = client.get(userinfo_url, headers=headers)
    resp.raise_for_status()
    user = resp.json()

    click.echo("👤 You are logged in as:")
    click.echo(user)


@cli.command()
def logout():
    auth.clear_cache()
    click.echo("👋 Logged out.")


if __name__ == "__main__":
    cli()
