import asyncio
import base64
import socket
import subprocess
import time
from pathlib import Path

import click
from developer_setup import (
    generate_developer_configs,
    load_developer_state,
    setup_developer_resources,
    teardown_developer_resources,
    write_developer_state,
)
from github_setup import generate_github_app_setup_guide
from ngrok import run_ngrok_tunnels


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--name", type=str, help="Developer name", required=True)
@click.option("--email", type=str, help="Developer email", required=True)
@click.option("--region", type=str, default="us", help="Ngrok region (default: us)")
@click.option(
    "--setup-github", is_flag=True, help="Setup GitHub resources", required=False
)
def setup(name: str, email: str, region: str, setup_github: bool) -> None:
    """Setup developer environment"""
    try:
        developer = setup_developer_resources(
            full_name=name, email=email, region=region, setup_github=setup_github
        )
        generate_developer_configs(name=name, output_dir="state/out")

        if setup_github:
            generate_github_app_setup_guide(developer.github_app)
            click.echo(
                "\n📝 Please follow the setup guide in state/out/github_app_setup_guide.md to create your GitHub App"
            )
            click.echo("Once you've completed the setup, press Enter to continue...")
            input()

            # Get GitHub client ID
            # app_id = click.prompt("Please enter your GitHub App ID", type=str)
            client_id = click.prompt("Please enter your GitHub App Client ID", type=str)
            client_secret = click.prompt(
                "Please enter your GitHub App Client Secret", type=str
            )

            # Get PEM file path
            raw_pem_path = click.prompt(
                "Please drag and drop your downloaded GitHub App private key (.pem file)",
                type=str,
            )

            # Clean the path from drag-and-drop
            pem_path = raw_pem_path.strip().strip("'").strip('"')

            # Validate the cleaned path
            try:
                click.Path(exists=True, file_okay=True, dir_okay=False).convert(
                    pem_path, None, None
                )
            except click.BadParameter as e:
                click.echo(f"❌ Error: {e}", err=True)
                return

            # Convert to absolute path
            pem_path = str(Path(pem_path).resolve())

            # Update developer state with GitHub credentials
            # developer.github_app.app_id = app_id
            developer.github_app.client_id = client_id.strip().strip(" ")
            developer.github_app.client_secret = client_secret.strip().strip(" ")
            developer.github_app.private_key_pem_path = pem_path

            # Read and base64 encode the PEM file
            with open(pem_path, "rb") as f:
                pem_content = f.read()
                base64_private_key_pem = base64.b64encode(pem_content).decode("utf-8")
                developer.github_app.base64_private_key_pem = base64_private_key_pem

            write_developer_state(developer)
            generate_developer_configs(name=name, output_dir="state/out")

            click.echo(
                "✅ GitHub App credentials have been saved to your developer state"
            )

        click.echo(f"✅ Successfully set up developer: {name}")
    except Exception as e:
        click.echo(f"❌ Error setting up developer: {e!s}", err=True)


@cli.command()
@click.option("--name", type=str, help="Developer name", required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="state/out",
    help="Directory to write config files to",
)
def generate_configs(name: str, output_dir: str) -> None:
    """Generate developer configs"""
    developer = load_developer_state(name)
    if not developer:
        click.echo(f"❌ No state file found for developer: {name}", err=True)
        return

    try:
        generate_developer_configs(name=name, output_dir=output_dir)
        click.echo(f"✅ Successfully generated configs for developer: {name}")
    except Exception as e:
        click.echo(f"❌ Error generating configs: {e!s}", err=True)


@cli.command()
@click.option("--name", type=str, help="Developer name", required=True)
def teardown(name: str) -> None:
    """Teardown developer environment"""
    developer = load_developer_state(name)
    if not developer:
        click.echo(f"❌ No state file found for developer: {name}", err=True)
        return

    if teardown_developer_resources(developer):
        click.echo(f"✅ Successfully tore down resources for: {name}")
    else:
        click.echo(f"❌ Some resources failed to tear down for: {name}", err=True)


def wait_for_socket_server(
    host: str = "localhost", port: int = 9000, timeout: int = 30
) -> bool:
    """Wait for the socket server to be ready to accept connections"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return True
        except OSError:
            pass
        time.sleep(1)
    return False


@cli.command()
@click.option("--name", type=str, help="Developer name", required=True)
@click.option(
    "--ports",
    type=str,
    help="Comma-separated list of ports to forward. Format: 'http:8000,tcp:9000'",
    required=True,
)
def run_tunnels(name: str, ports: str) -> None:
    """Run ngrok tunnels for each domain and TCP address"""
    developer = load_developer_state(name)
    if not developer:
        click.echo(f"❌ No state file found for developer: {name}", err=True)
        return

    try:
        # Parse ports and separate HTTP and TCP ports
        http_ports: list[int] = []
        tcp_ports: list[int] = []

        for port_spec in ports.split(","):
            port_spec = port_spec.strip()
            if ":" not in port_spec:
                click.echo(
                    f"❌ Invalid port specification: {port_spec}. Must be in format 'http:8000' or 'tcp:9000'",
                    err=True,
                )
                return

            port_type, port = port_spec.split(":")
            try:
                port_num = int(port.strip())
                if port_type.lower() == "http":
                    http_ports.append(port_num)
                elif port_type.lower() == "tcp":
                    tcp_ports.append(port_num)
                else:
                    click.echo(
                        f"❌ Invalid port type: {port_type}. Must be 'http' or 'tcp'",
                        err=True,
                    )
                    return
            except ValueError:
                click.echo(f"❌ Invalid port number: {port}", err=True)
                return

        # Get domains and TCP addresses from developer state
        domains = developer.reserved_domains
        tcp_address = developer.reserved_tcp_address

        if not domains and not tcp_address:
            click.echo(
                "❌ No domains or TCP address found in developer state", err=True
            )
            return

        if len(domains) != len(http_ports):
            click.echo(
                f"❌ Number of domains ({len(domains)}) does not match number of HTTP ports ({len(http_ports)})",
                err=True,
            )
            return

        if len(tcp_ports) > 1:
            click.echo(
                "❌ Only one TCP port can be specified since there is only one reserved TCP address",
                err=True,
            )
            return

        if tcp_ports and not tcp_address:
            click.echo(
                "❌ TCP port specified but no TCP address found in developer state",
                err=True,
            )
            return

        # Start ngrok server in the background
        click.echo("🚀 Starting ngrok server...")
        server_process = subprocess.Popen(
            ["uvicorn", "src.ngrok_server:app", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        click.echo("⏳ Waiting for socket server to start...")
        if not wait_for_socket_server():
            click.echo("❌ Socket server failed to start within timeout", err=True)
            server_process.terminate()
            server_process.wait()
            return

        click.echo("🌐 Ngrok server is running at: http://localhost:8000")
        click.echo("⚙️ GitHub app setup guide running at: http://localhost:8000/github")
        click.echo("🔌 Connecting to tunnel manager...")
        click.echo("Press Ctrl+C to stop all tunnels")

        # Run the tunnels using asyncio.run
        try:
            asyncio.run(
                run_ngrok_tunnels(
                    domains=domains,
                    http_ports=http_ports,
                    tcp_addresses=[tcp_address] if tcp_address and tcp_ports else [],
                    tcp_ports=tcp_ports,
                )
            )
        except KeyboardInterrupt:
            click.echo("\n👋 Stopping tunnels...")
        except ConnectionRefusedError:
            click.echo(
                "❌ Could not connect to tunnel manager. Make sure 'uvicorn src.ngrok_server:app --reload' is running",
                err=True,
            )
        except Exception as e:
            click.echo(f"❌ Error running tunnels: {e!s}", err=True)
        finally:
            # Cleanup: stop the server process
            server_process.terminate()
            server_process.wait()

    except Exception as e:
        click.echo(f"❌ Error setting up tunnels: {e!s}", err=True)


if __name__ == "__main__":
    cli()
