# Purpose
This file is an HTML document that serves as a user interface for managing Ngrok tunnels. It provides a web-based control panel with buttons to check the status, stop, and start all Ngrok tunnels, indicating its narrow functionality focused on tunnel management. The document includes embedded CSS for styling and JavaScript for dynamic interactions, such as connecting to a WebSocket server to receive real-time updates and sending commands to a backend server via HTTP requests. The common theme of the file is to facilitate user interaction with Ngrok tunnels through a visually organized and interactive web page. This file is relevant to the codebase as it provides the front-end interface for users to manage and monitor Ngrok tunnels, integrating with backend services to perform these operations.
# Content Summary
The provided HTML document is a user interface for managing Ngrok tunnels, featuring a web-based control panel. The document is structured with HTML, CSS, and JavaScript to facilitate interaction with a server through WebSocket and HTTP requests.

### Key Components:

1. **HTML Structure**: 
   - The document is defined as an HTML5 document with a `<head>` section containing metadata and a `<style>` block for CSS.
   - The `<body>` includes a header (`<h1>`) titled "Ngrok Tunnel Manager" and two main sections: a control panel (`<div class="controls">`) and a log display area (`<div id="log">`).

2. **CSS Styling**:
   - The page uses a modern, responsive design with a maximum width of 1200px, centered content, and a light gray background.
   - The control panel and log area are styled with white and dark themes, respectively, using box shadows and border-radius for a polished look.
   - Buttons are styled with a blue background, white text, and a hover effect that darkens the button color.

3. **JavaScript Functionality**:
   - **WebSocket Connection**: The script establishes a WebSocket connection to the server at the path `/ws`. It handles connection events to update the status display, attempting to reconnect every 3 seconds if disconnected.
   - **Command Execution**: The interface provides three buttons to send commands to the server: "Status", "Stop All", and "Start All". These buttons trigger the `sendCommand` function, which makes HTTP requests to the respective endpoints (`/status`, `/stop`, `/start`) and updates the status display based on the server's response.
   - **Log Display**: Incoming messages from the WebSocket are appended to the log area, which automatically scrolls to show the latest entries.

4. **User Interaction**:
   - Users can interact with the control panel to manage Ngrok tunnels, receiving real-time feedback on the connection status and command results.
   - The interface is designed to be intuitive, with clear visual cues for connection status and command execution results.

This document serves as a front-end interface for managing Ngrok tunnels, providing real-time interaction and feedback through a combination of WebSocket and HTTP communication.
