import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active connections
clients: dict[str, asyncio.Queue] = {}
websockets: set[WebSocket] = set()


async def broadcast(message: str) -> None:
    """Send a message to all connected WebSocket clients"""
    disconnected = set()
    for websocket in websockets:
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            disconnected.add(websocket)

    # Remove disconnected clients
    websockets.difference_update(disconnected)


async def send_command_to_clients(command: str) -> None:
    """Send a command to all tunnel clients and wait for responses"""
    if not clients:
        await broadcast(
            json.dumps({"type": "status", "data": "No tunnel clients connected"})
        )
        return

    print(f"Sending command {command} to {len(clients)} clients")
    for client_id, queue in clients.items():
        try:
            await queue.put(f"COMMAND:{command}")
        except Exception as e:
            print(f"Error sending command to client {client_id}: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    websockets.add(websocket)
    print(f"New WebSocket connection established. Total connections: {len(websockets)}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received command: {data}")
            await send_command_to_clients(data)
    except WebSocketDisconnect:
        websockets.remove(websocket)
        print(f"WebSocket disconnected. Remaining connections: {len(websockets)}")


async def handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Handle incoming tunnel client connections"""
    client_id = (
        f"{writer.get_extra_info('peername')[0]}:{writer.get_extra_info('peername')[1]}"
    )
    queue = asyncio.Queue()
    clients[client_id] = queue
    print(f"New tunnel client connected: {client_id}")

    # Notify websocket clients about new connection
    await broadcast(
        json.dumps({"type": "log", "data": f"Tunnel client connected: {client_id}"})
    )

    try:
        while True:
            try:
                # Wait for a command from the WebSocket
                command = await queue.get()
                print(f"Sending command to tunnel client {client_id}: {command}")

                writer.write(f"{command}\n".encode())
                await writer.drain()

                # Read response from tunnel client
                response = await reader.readline()
                if not response:
                    print(f"Client {client_id} closed connection")
                    break

                response_text = response.decode().strip()
                print(f"Received response from {client_id}: {response_text}")

                if response_text.startswith("Status:"):
                    await broadcast(
                        json.dumps({"type": "status", "data": response_text})
                    )
                else:
                    await broadcast(json.dumps({"type": "log", "data": response_text}))

            except ConnectionResetError:
                print(f"Connection reset for client {client_id}")
                break
            except Exception as e:
                print(f"Error handling client {client_id}: {e}")
                break

    finally:
        if client_id in clients:
            del clients[client_id]
            print(f"Tunnel client disconnected: {client_id}")
            await broadcast(
                json.dumps(
                    {"type": "log", "data": f"Tunnel client disconnected: {client_id}"}
                )
            )

        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Error closing writer for client {client_id}: {e}")


async def start_socket_server() -> None:
    """Start the socket server for tunnel clients"""
    server = await asyncio.start_server(handle_client, "localhost", 9000)
    print("Socket server started on localhost:9000")
    async with server:
        await server.serve_forever()


@app.on_event("startup")
async def startup_event() -> None:
    """Start the socket server when the FastAPI app starts"""
    task = asyncio.create_task(start_socket_server())
    # Store the task reference to prevent it from being garbage collected
    app.state.socket_server_task = task


@app.get("/", response_class=HTMLResponse)
async def get() -> HTMLResponse:
    """Serve the main UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ngrok Tunnel Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .controls { margin: 20px 0; }
            button { margin: 0 10px; padding: 10px 20px; }
            #log {
                background: #f5f5f5;
                padding: 10px;
                height: 400px;
                overflow-y: auto;
                white-space: pre-wrap;
                font-family: monospace;
            }
            .status { color: #666; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Ngrok Tunnel Manager</h1>
        <div class="controls">
            <button onclick="sendCommand('status')">Status</button>
            <button onclick="sendCommand('stop')">Stop All</button>
            <button onclick="sendCommand('start')">Start All</button>
        </div>
        <div id="status" class="status">Waiting for connection...</div>
        <div id="log"></div>
        <script>
            let ws = null;
            let reconnectAttempts = 0;
            const maxReconnectDelay = 5000;

            function connect() {
                console.log("Connecting to WebSocket...");
                ws = new WebSocket(`ws://${window.location.host}/ws`);

                ws.onopen = function() {
                    console.log("WebSocket connected");
                    document.getElementById('status').textContent = 'Connected';
                    reconnectAttempts = 0;
                };

                ws.onmessage = function(event) {
                    console.log("Received message:", event.data);
                    const data = JSON.parse(event.data);
                    if (data.type === 'status') {
                        document.getElementById('status').textContent = data.data;
                    } else {
                        const log = document.getElementById('log');
                        log.textContent += data.data + '\\n';
                        log.scrollTop = log.scrollHeight;
                    }
                };

                ws.onclose = function() {
                    console.log("WebSocket disconnected");
                    document.getElementById('status').textContent = 'Disconnected. Reconnecting...';
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxReconnectDelay);
                    reconnectAttempts++;
                    setTimeout(connect, delay);
                };

                ws.onerror = function(error) {
                    console.error("WebSocket error:", error);
                };
            }

            function sendCommand(command) {
                console.log("Sending command:", command);
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(command);
                    document.getElementById('status').textContent = `Sending ${command} command...`;
                } else {
                    console.log("WebSocket not ready");
                    document.getElementById('status').textContent = 'Not connected. Retrying...';
                    connect();
                }
            }

            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
