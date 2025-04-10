import asyncio
import json
import socket
import subprocess
import time
from pathlib import Path

import click
from developer_setup import (
    create_developer_resource_configs,
    setup_developer_resources,
    teardown_developer_resources,
)
from models import Developer
from ngrok import run_ngrok_tunnels


def load_developer_state(full_name: str) -> Developer | None:
    filename = f"{full_name.lower().replace(' ', '_')}_state.json"
    file_path = Path("state") / filename

    if not file_path.exists():
        print(f"❌ No state file found for developer: {full_name}")
        return None

    try:
        with open(file_path) as f:
            state = json.load(f)
            return Developer.model_validate(state)
    except Exception as e:
        print(f"❌ Error loading state file: {e!s}")
        return None


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--name", type=str, help="Developer name", required=True)
@click.option("--email", type=str, help="Developer email", required=True)
@click.option("--region", type=str, default="us", help="Ngrok region (default: us)")
def setup(name: str, email: str, region: str) -> None:
    """Setup developer environment"""
    try:
        setup_developer_resources(full_name=name, email=email, region=region)
        click.echo(f"✅ Successfully set up developer: {name}")
    except Exception as e:
        click.echo(f"❌ Error setting up developer: {e!s}", err=True)


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
    """Generate resource config files for a developer"""
    developer = load_developer_state(name)
    if not developer:
        click.echo(f"❌ No state file found for developer: {name}", err=True)
        return

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate configs
    configs = create_developer_resource_configs(developer)

    # Create markdown guide
    guide_file = output_path / "setup_guide.md"
    with open(guide_file, "w") as f:
        f.write(f"# Setup Guide for {developer.full_name}\n\n")
        f.write("## Overview\n\n")
        f.write(
            "This guide will help you set up your development environment with the following resources:\n\n"
        )

        # List all resources
        for resource_name in configs:
            f.write(f"- {resource_name.replace('-', ' ').title()}\n")

        f.write("\n## Configuration Files\n\n")
        f.write("The following configuration files have been generated:\n\n")

        # Write config files and document them
        for resource_name, config in configs.items():
            config_file = (
                output_path / f"{resource_name.lower().replace(' ', '_')}_config.json"
            )
            with open(config_file, "w") as cf:
                json.dump(config, cf, indent=2)
            click.echo(f"✅ Wrote {resource_name} config to {config_file}")

            # Add to markdown guide
            f.write(f"### {resource_name.replace('-', ' ').title()}\n\n")
            f.write(f"Configuration file: `{config_file.name}`\n\n")

            if resource_name == "github-app":
                click.echo(f"📝 {resource_name} Configuration:")
                click.echo("```json")
                click.echo(json.dumps(config, indent=2))
                click.echo("```\n")

                f.write("#### GitHub App Configuration\n\n")
                f.write("```json\n")
                f.write(json.dumps(config, indent=2))
                f.write("\n```\n\n")
                f.write("To set up the GitHub App:\n")
                f.write("1. Go to GitHub Developer Settings\n")
                f.write("2. Create a new GitHub App\n")
                f.write(
                    "3. Use the configuration above to fill in the required fields\n"
                )
                f.write("4. Generate and download the private key\n")
                f.write("5. Update the `private_key_pem_path` in the config file\n\n")

            if "env" in config:
                click.echo(f"\n📝 {resource_name} Environment Variables (.env format):")
                click.echo("```")
                for key, value in config["env"].items():
                    click.echo(f"{key}={value}")
                click.echo("```\n")

                f.write("#### Environment Variables\n\n")
                f.write("Add these variables to your `.env` file:\n\n")
                f.write("```\n")
                for key, value in config["env"].items():
                    f.write(f"{key}={value}\n")
                f.write("```\n\n")

            if resource_name == "webapp-frontend" and "vite_config" in config:
                click.echo(
                    f"📝 {resource_name} Vite Configuration (vite.config.ts format):"
                )
                click.echo("```typescript")
                click.echo("import { defineConfig } from 'vite'")
                click.echo("import react from '@vitejs/plugin-react'")
                click.echo("\n// https://vitejs.dev/config/")
                click.echo("export default defineConfig({")
                click.echo("  plugins: [react()],")
                click.echo("  server: {")
                for key, value in config["vite_config"]["server"].items():
                    if isinstance(value, list):
                        click.echo(f"    {key}: {json.dumps(value)},")
                    else:
                        click.echo(f"    {key}: {json.dumps(value)},")
                click.echo("  }")
                click.echo("})")
                click.echo("```\n")

                f.write("#### Vite Configuration\n\n")
                f.write("Add this configuration to your `vite.config.ts`:\n\n")
                f.write("```typescript\n")
                f.write("import { defineConfig } from 'vite'\n")
                f.write("import react from '@vitejs/plugin-react'\n\n")
                f.write("// https://vitejs.dev/config/\n")
                f.write("export default defineConfig({\n")
                f.write("  plugins: [react()],\n")
                f.write("  server: {\n")
                for key, value in config["vite_config"]["server"].items():
                    if isinstance(value, list):
                        f.write(f"    {key}: {json.dumps(value)},\n")
                    else:
                        f.write(f"    {key}: {json.dumps(value)},\n")
                f.write("  }\n")
                f.write("})\n")
                f.write("```\n\n")

            f.write("---\n\n")

    click.echo(f"✅ Created setup guide: {guide_file}")


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
    "--ports", type=str, help="Comma-separated list of ports to forward", required=True
)
def run_tunnels(name: str, ports: str) -> None:
    """Run ngrok tunnels for each domain"""
    developer = load_developer_state(name)
    if not developer:
        click.echo(f"❌ No state file found for developer: {name}", err=True)
        return

    try:
        # Parse ports
        port_list = [int(p.strip()) for p in ports.split(",")]

        # Get domains from developer state
        domains = developer.reserved_domains

        if not domains:
            click.echo("❌ No domains found in developer state", err=True)
            return

        if len(domains) != len(port_list):
            click.echo(
                f"❌ Number of domains ({len(domains)}) does not match number of ports ({len(port_list)})",
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
            asyncio.run(run_ngrok_tunnels(domains, port_list))
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
