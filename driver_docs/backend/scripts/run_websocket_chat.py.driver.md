# Purpose
This Python script is designed to facilitate a WebSocket-based chat application. It primarily focuses on establishing a connection to a WebSocket server, sending periodic "KEEP_ALIVE" messages to maintain the connection, and handling user input to send messages through the WebSocket. The script uses the `asyncio` library to manage asynchronous operations, ensuring that the chat application remains responsive while waiting for user input or server responses. The `websockets` library is employed to handle the WebSocket connection, and the script includes error handling to manage connection issues gracefully.

The script is structured as an executable script, with a `main` function that initiates the chat application by calling `run_websocket_chat`. It requires an authentication token, which is hardcoded but can be modified to prompt the user if necessary. The script sends a setup message containing node IDs upon establishing a connection and continuously listens for server responses, printing them to the console. The use of asynchronous tasks, such as the `send_keep_alive` function, ensures that the connection remains active without blocking other operations. This script is intended for direct execution rather than as a library, as indicated by the `if __name__ == "__main__":` block.
# Imports and Dependencies

---
- `asyncio`
- `json`
- `websockets`


# Global Variables

---
### AUTH_TOKEN 
- **Type**: `string`
- **Description**: `AUTH_TOKEN` is a global variable that stores a JSON Web Token (JWT) as a string. This token is used for authenticating the user when connecting to a WebSocket server.
- **Use**: The `AUTH_TOKEN` is used to authenticate the WebSocket connection by being included in the Authorization header.


---
### KEEP_ALIVE_INTERVAL 
- **Type**: `int`
- **Description**: `KEEP_ALIVE_INTERVAL` is an integer variable that specifies the time interval, in seconds, between sending keep-alive messages over a websocket connection. It is set to 30, meaning a keep-alive message will be sent every 30 seconds.
- **Use**: This variable is used in the `send_keep_alive` asynchronous function to determine the sleep duration between sending 'KEEP_ALIVE' messages to maintain the websocket connection.


---
### NODE_IDS 
- **Type**: `list`
- **Description**: `NODE_IDS` is a list containing a single string element, which is a UUID (Universally Unique Identifier). This UUID is used to uniquely identify a node in a network or system.
- **Use**: This variable is used to send a setup message containing node identifiers over a websocket connection.


# Functions

---
### main 
The `main` function initiates the asynchronous execution of a websocket chat client.
- **Inputs**:
    - None
- **Control Flow**:
    - The function `main` is defined without any parameters.
    - It calls `asyncio.run()` with `run_websocket_chat()` as its argument, which starts the asynchronous event loop and runs the `run_websocket_chat` coroutine.
- **Output**:
    - The function does not return any value; it serves as the entry point to start the websocket chat client.


---
### run_websocket_chat 
The `run_websocket_chat` function establishes a WebSocket connection to a chat server, sends a setup message, and facilitates a chat session with keep-alive messages.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if an authorization token is available; if not, prompt the user for one.
    - If no token is provided, print a message and exit the function.
    - Define the WebSocket URI and print a connection message.
    - Attempt to import the `websockets` library, and exit if not found.
    - Establish a WebSocket connection with the server using the provided token for authorization.
    - Start a keep-alive task to periodically send keep-alive messages to the server.
    - Send a setup message containing node IDs to the server.
    - Enter a loop to continuously read user input and send it to the server until an empty input is received.
    - Within the input loop, enter another loop to receive and print server responses until a 'GENERATION_COMPLETE' message is received.
    - Handle `websockets.ConnectionClosed` exception by printing a message when the connection is closed by the server.
    - Cancel the keep-alive task when exiting the chat session.
- **Output**:
    - The function does not return any value; it performs I/O operations to facilitate a WebSocket chat session.


---
### send_keep_alive 
The `send_keep_alive` function continuously sends a 'KEEP_ALIVE' message to a websocket at regular intervals to maintain the connection.
- **Inputs**:
    - `websocket`: An active websocket connection object to which the 'KEEP_ALIVE' message will be sent.
- **Control Flow**:
    - The function enters an infinite loop to repeatedly perform its operations.
    - Within the loop, it first pauses execution for a duration specified by `KEEP_ALIVE_INTERVAL`.
    - After the pause, it attempts to send a 'KEEP_ALIVE' message through the provided websocket.
    - If an exception occurs during the sending process, it prints an error message and breaks out of the loop, effectively stopping the keep-alive process.
- **Output**:
    - The function does not return any value; it operates asynchronously to maintain the websocket connection by sending periodic messages.


