# Purpose
This Python file is a FastAPI application designed to manage WebSocket connections and tunnel client communications, specifically for an Ngrok Tunnel Manager. The application serves as both a WebSocket server and a socket server, facilitating real-time communication between a web-based user interface and tunnel clients. The FastAPI framework is used to define the web server, which serves static files and HTML content, and manages WebSocket connections. The application maintains a set of active WebSocket connections and a dictionary of tunnel clients, allowing it to broadcast messages and commands to all connected clients. The WebSocket endpoint listens for incoming messages, which are then relayed to the tunnel clients, and responses from these clients are broadcast back to all WebSocket connections.

The application includes several key components: a WebSocket endpoint for handling real-time communication with the web interface, a socket server for managing tunnel client connections, and a startup event to initialize the socket server when the FastAPI app starts. The HTML content served by the application provides a user interface for sending commands to the tunnel clients and displays logs and status updates received from them. The JavaScript embedded in the HTML manages the WebSocket connection, handling events such as connection, message reception, and reconnection attempts. This code is a comprehensive solution for managing tunnel connections and facilitating communication between a web interface and multiple clients, making it suitable for applications that require real-time updates and command execution across distributed systems.
# Imports and Dependencies

---
- `asyncio`
- `json`
- `fastapi.FastAPI`
- `fastapi.WebSocket`
- `fastapi.WebSocketDisconnect`
- `fastapi.responses.HTMLResponse`
- `fastapi.staticfiles.StaticFiles`


# Global Variables

---
### app 
- **Type**: `FastAPI`
- **Description**: The `app` variable is an instance of the FastAPI class, which is used to create a web application. It serves as the main entry point for defining routes, handling requests, and managing the lifecycle of the application.
- **Use**: This variable is used to define and configure the web application, including setting up routes, handling WebSocket connections, and managing application events.


---
### clients 
- **Type**: `dict[str, asyncio.Queue]`
- **Description**: The `clients` variable is a dictionary that maps client identifiers (as strings) to asyncio.Queue objects. Each entry in the dictionary represents a connected tunnel client, with the queue being used to send commands to the client.
- **Use**: This variable is used to manage and send commands to connected tunnel clients in the application.


---
### websockets 
- **Type**: `set[WebSocket]`
- **Description**: The `websockets` variable is a global set that stores active WebSocket connections. It is used to keep track of all currently connected WebSocket clients, allowing the server to broadcast messages to all clients or handle disconnections.
- **Use**: This variable is used to manage and iterate over active WebSocket connections for broadcasting messages and handling disconnections.


# Functions

---
### broadcast 
The `broadcast` function sends a message to all connected WebSocket clients and removes any clients that have disconnected.
- **Inputs**:
    - `message`: A string representing the message to be sent to all connected WebSocket clients.
- **Control Flow**:
    - Initialize an empty set `disconnected` to keep track of WebSocket clients that have disconnected.
    - Iterate over each `websocket` in the global `websockets` set.
    - Attempt to send the `message` to the current `websocket` using `await websocket.send_text(message)`.
    - If a `WebSocketDisconnect` exception is raised, add the `websocket` to the `disconnected` set.
    - After attempting to send the message to all clients, remove the disconnected clients from the `websockets` set using `websockets.difference_update(disconnected)`.
- **Output**:
    - The function does not return any value; it performs its operations asynchronously and modifies the global `websockets` set in place.


---
### get 
The `get` function serves the main user interface for the Ngrok Tunnel Manager as an HTML response.
- **Inputs**:
    - None
- **Control Flow**:
    - The function defines a multi-line string `html_content` containing HTML and JavaScript code for the user interface.
    - The HTML includes a title, styles, and a body with buttons for controlling the Ngrok tunnels and a log area.
    - JavaScript within the HTML manages WebSocket connections to send commands and receive status updates.
    - The function returns an `HTMLResponse` with the `html_content` as its content.
- **Output**:
    - The function returns an `HTMLResponse` containing the HTML content for the main UI of the Ngrok Tunnel Manager.


---
### get_github_setup 
The `get_github_setup` function asynchronously returns an HTML response by reading the content of a static HTML file named 'gh.html' located in the 'static' directory.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as asynchronous, allowing it to be used in an asynchronous context.
    - It opens the file 'static/gh.html' in read mode.
    - The content of the file is read and used to create an `HTMLResponse` object.
    - The `HTMLResponse` object is returned as the output of the function.
- **Output**:
    - The function returns an `HTMLResponse` object containing the HTML content of the 'gh.html' file.


---
### handle_client 
The `handle_client` function manages the lifecycle of a tunnel client connection, handling communication between the client and WebSocket clients.
- **Inputs**:
    - `reader`: An `asyncio.StreamReader` object used to read data from the tunnel client.
    - `writer`: An `asyncio.StreamWriter` object used to send data to the tunnel client.
- **Control Flow**:
    - The function starts by generating a unique `client_id` using the client's peer name and initializes a queue for the client, storing it in the global `clients` dictionary.
    - A message is broadcasted to all WebSocket clients notifying them of the new tunnel client connection.
    - The function enters a loop where it waits for commands from the WebSocket clients via the queue.
    - For each command, it sends the command to the tunnel client and waits for a response.
    - If a response is received, it is decoded and broadcasted to WebSocket clients, with special handling if the response starts with 'Status:'.
    - The loop continues until the connection is closed by the client or an error occurs, at which point the client is removed from the `clients` dictionary and a disconnection message is broadcasted.
    - Finally, the writer is closed and any exceptions during closure are logged.
- **Output**:
    - The function does not return any value; it performs side effects such as managing client connections and broadcasting messages.


---
### send_command_to_clients 
The function `send_command_to_clients` sends a specified command to all connected tunnel clients and handles any exceptions that occur during the process.
- **Inputs**:
    - `command`: A string representing the command to be sent to all tunnel clients.
- **Control Flow**:
    - Check if there are any connected clients; if not, broadcast a status message indicating no clients are connected and return.
    - Print a message indicating the command being sent and the number of clients.
    - Iterate over each client in the `clients` dictionary, attempting to put the command into each client's queue.
    - If an exception occurs while sending a command to a client, print an error message with the client ID and exception details.
- **Output**:
    - The function does not return any value; it performs actions such as broadcasting messages and printing to the console.


---
### start_socket_server 
The function `start_socket_server` initializes and starts an asynchronous socket server on localhost at port 9000 to handle tunnel client connections.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses `asyncio.start_server` to create a server that listens for connections on 'localhost' at port 9000, with `handle_client` as the callback for handling incoming connections.
    - A message is printed to the console indicating that the socket server has started.
    - The server is run within an asynchronous context manager using `async with server`, ensuring that the server is properly closed when the context is exited.
    - The server is set to run indefinitely using `await server.serve_forever()`, which keeps the server active and listening for incoming connections.
- **Output**:
    - The function does not return any value; it runs the server indefinitely to handle client connections.


---
### startup_event 
The `startup_event` function initializes and starts the socket server when the FastAPI application starts.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is decorated with `@app.on_event('startup')`, indicating it runs when the FastAPI app starts.
    - It creates an asynchronous task to start the socket server by calling `start_socket_server()`.
    - The task is stored in `app.state.socket_server_task` to prevent it from being garbage collected.
- **Output**:
    - The function does not return any output.


---
### websocket_endpoint 
The `websocket_endpoint` function manages WebSocket connections, receiving commands from clients and forwarding them to tunnel clients.
- **Inputs**:
    - `websocket`: A WebSocket object representing the connection to a client.
- **Control Flow**:
    - The function begins by accepting the WebSocket connection and adding it to the set of active connections.
    - It enters a loop where it continuously waits to receive text data from the WebSocket.
    - Upon receiving data, it logs the command and calls `send_command_to_clients` to forward the command to all connected tunnel clients.
    - If a `WebSocketDisconnect` exception is raised, indicating the client has disconnected, the WebSocket is removed from the active connections set and a disconnection message is logged.
- **Output**:
    - The function does not return any value; it operates asynchronously to manage WebSocket connections and command forwarding.


