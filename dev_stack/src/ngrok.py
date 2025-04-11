import asyncio
import re
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import TextIO

# 1. Authenticate
# 2. Create 2 reserved domain
# 3. Create 1 reserved tcp address
import httpx
from models import (
    DomainStatus,
    NgrokReservedDomain,
    NgrokReservedTcpAddress,
)

NGROK_BASE_API_URL = "https://api.ngrok.com"


def create_reserved_domain(
    api_key: str, subdomain: str, description: str, region: str = "us"
) -> dict:
    ngrok_api_url = f"{NGROK_BASE_API_URL}/reserved_domains"
    full_domain = f"{subdomain}.ngrok.io"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Ngrok-Version": "2",
    }

    data = {
        "domain": full_domain,
        "region": region,
        "description": description,
    }

    response = httpx.post(ngrok_api_url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ Reserved domain created: {full_domain}")
        return response.json()
    elif response.status_code == 409:
        print(f"⚠️ Domain already taken: {full_domain}")
        return response.json()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        response.raise_for_status()


def generate_unique_subdomain(
    developer_name: str, prefix: str = "app", suffix_length: int = 4
) -> str:
    # Sanitize the developer name
    sanitized_name = re.sub(
        r"[^a-z0-9\-]", "", developer_name.lower().replace(" ", "-")
    )
    sanitized_prefix = re.sub(r"[^a-z0-9\-]", "", prefix.lower().replace(" ", "-"))
    return f"{sanitized_name}-{sanitized_prefix}"


def delete_reserved_domain(api_key: str, domain_id: str) -> bool:
    ngrok_api_url = f"{NGROK_BASE_API_URL}/reserved_domains/{domain_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Ngrok-Version": "2",
    }

    try:
        response = httpx.delete(ngrok_api_url, headers=headers)
        if response.status_code == 204:
            print(f"✅ Successfully deleted reserved domain with ID: {domain_id}")
            return True
        else:
            print(
                f"❌ Failed to delete reserved domain. Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print(f"❌ Error deleting reserved domain: {e!s}")
        return False


def create_reserved_tcp_address(
    api_key: str, description: str, region: str = "us", metadata: str | None = None
) -> NgrokReservedTcpAddress:
    ngrok_api_url = f"{NGROK_BASE_API_URL}/reserved_addrs"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Ngrok-Version": "2",
    }

    data = {
        "description": description,
        "region": region,
    }

    if metadata:
        data["metadata"] = metadata

    response = httpx.post(ngrok_api_url, headers=headers, json=data)

    if response.status_code == 201:
        print("✅ Reserved TCP address created successfully")
        result = response.json()
        return NgrokReservedTcpAddress(
            address=result["addr"],
            description=description,
            region=region,
            status=DomainStatus.CREATED,
            metadata=result,
        )
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        response.raise_for_status()


def delete_reserved_tcp_address(api_key: str, address_id: str) -> bool:
    ngrok_api_url = f"{NGROK_BASE_API_URL}/reserved_addrs/{address_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Ngrok-Version": "2",
    }

    try:
        response = httpx.delete(ngrok_api_url, headers=headers)
        if response.status_code == 204:
            print(f"✅ Successfully deleted reserved TCP address with ID: {address_id}")
            return True
        else:
            print(
                f"❌ Failed to delete reserved TCP address. Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print(f"❌ Error deleting reserved TCP address: {e!s}")
        return False


@contextmanager
def prefixed_output(prefix: str) -> Generator[None, None, None]:
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    class PrefixedStream:
        def __init__(self, original: TextIO, prefix: str) -> None:
            self.original = original
            self.prefix = prefix

        def write(self, text: str) -> None:
            if text.strip():
                self.original.write(f"[{self.prefix}] {text}")
            else:
                self.original.write(text)

        def flush(self) -> None:
            self.original.flush()

        def fileno(self) -> int:
            return self.original.fileno()

    prefixed_stdout = PrefixedStream(original_stdout, prefix)
    prefixed_stderr = PrefixedStream(original_stderr, prefix)

    sys.stdout = prefixed_stdout
    sys.stderr = prefixed_stderr

    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


class TunnelManager:
    def __init__(
        self,
        domains: list[NgrokReservedDomain],
        http_ports: list[int],
        tcp_addresses: list[NgrokReservedTcpAddress],
        tcp_ports: list[int],
    ) -> None:
        if len(domains) != len(http_ports):
            raise ValueError("Number of domains must match number of HTTP ports")
        if len(tcp_addresses) != len(tcp_ports):
            raise ValueError("Number of TCP addresses must match number of TCP ports")

        self.domains = domains
        self.http_ports = http_ports
        self.tcp_addresses = tcp_addresses
        self.tcp_ports = tcp_ports
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self.tasks: list[asyncio.Task] = []
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._connected = asyncio.Event()

    async def send_message(self, message: str) -> None:
        """Send a message to the server"""
        if self.writer:
            try:
                self.writer.write(f"{message}\n".encode())
                await self.writer.drain()
            except Exception as e:
                print(f"Error sending message: {e}")

    async def run_tunnel(self, domain: NgrokReservedDomain, port: int) -> None:
        """Run a single HTTP ngrok tunnel"""
        # Wait for server connection before starting tunnel
        await self._connected.wait()

        cmd = ["ngrok", "http", "--domain", domain.domain, str(port)]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        self.processes[domain.domain] = proc
        await self.send_message(
            f"Started HTTP tunnel for {domain.domain} on port {port}"
        )

        try:
            while True:
                if proc.stdout:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    output = line.decode().strip()
                    await self.send_message(f"[{domain.domain}] {output}")
        except Exception as e:
            await self.send_message(f"Error in HTTP tunnel {domain.domain}: {e}")
        finally:
            self.processes.pop(domain.domain, None)

    async def run_tcp_tunnel(
        self, tcp_address: NgrokReservedTcpAddress, port: int
    ) -> None:
        """Run a single TCP ngrok tunnel"""
        # Wait for server connection before starting tunnel
        await self._connected.wait()

        cmd = ["ngrok", "tcp", "--remote-addr", tcp_address.address, str(port)]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        self.processes[tcp_address.address] = proc
        await self.send_message(
            f"Started TCP tunnel for {tcp_address.address} on port {port}"
        )

        try:
            while True:
                if proc.stdout:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    output = line.decode().strip()
                    await self.send_message(f"[{tcp_address.address}] {output}")
        except Exception as e:
            await self.send_message(f"Error in TCP tunnel {tcp_address.address}: {e}")
        finally:
            self.processes.pop(tcp_address.address, None)

    async def start_all_tunnels(self) -> None:
        """Start all HTTP and TCP tunnels"""
        # Start HTTP tunnels
        for domain, port in zip(self.domains, self.http_ports):
            if domain.domain not in self.processes:
                self.tasks.append(asyncio.create_task(self.run_tunnel(domain, port)))

        # Start TCP tunnels
        for tcp_address, port in zip(self.tcp_addresses, self.tcp_ports):
            if tcp_address.address not in self.processes:
                self.tasks.append(
                    asyncio.create_task(self.run_tcp_tunnel(tcp_address, port))
                )

    async def stop_all_tunnels(self) -> None:
        """Stop all tunnels"""
        for proc in self.processes.values():
            proc.terminate()
        await asyncio.gather(*(proc.wait() for proc in self.processes.values()))
        self.processes.clear()
        await self.send_message("All tunnels stopped")

    async def get_status(self) -> None:
        """Get status of all tunnels"""
        status = (
            ", ".join(
                f"{name}: {'running' if proc.returncode is None else 'stopped'}"
                for name, proc in self.processes.items()
            )
            or "No active tunnels"
        )
        await self.send_message(f"Status: {status}")

    async def handle_command(self, command: str) -> None:
        """Handle commands from the server"""
        commands = {
            "status": self.get_status,
            "stop": self.stop_all_tunnels,
            "start": self.start_all_tunnels,
        }

        handler = commands.get(command)
        if handler:
            await handler()
        else:
            await self.send_message(f"Unknown command: {command}")

    async def connect_to_server(self) -> None:
        """Connect to the FastAPI server and handle commands"""
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    "localhost", 9000
                )
                await self.send_message("Connected to server")
                self._connected.set()  # Signal that we're connected

                while True:
                    if self.reader:
                        data = await self.reader.readline()
                        if not data:
                            break
                        msg = data.decode().strip()
                        if msg.startswith("COMMAND:"):
                            command = msg.split("COMMAND:", 1)[1]
                            await self.handle_command(command)
            except ConnectionRefusedError:
                print("Could not connect to tunnel manager server. Is it running?")
                raise
            except Exception as e:
                print(f"Connection error: {e}, retrying in 5s...")
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()
                self.reader = None
                self.writer = None
                self._connected.clear()  # Signal that we're disconnected
                await asyncio.sleep(5)

    async def run(self) -> None:
        """Run the tunnel manager"""
        try:
            server_task = asyncio.create_task(self.connect_to_server())
            self.tasks.append(server_task)

            # Start tunnels after server connection
            await self._connected.wait()
            await self.start_all_tunnels()

            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            await self.stop_all_tunnels()
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()


async def run_ngrok_tunnels(
    domains: list[NgrokReservedDomain],
    http_ports: list[int],
    tcp_addresses: list[NgrokReservedTcpAddress],
    tcp_ports: list[int],
) -> None:
    """Main entry point for running ngrok tunnels"""
    manager = TunnelManager(domains, http_ports, tcp_addresses, tcp_ports)
    await manager.run()
