# Purpose
This Python code file is designed to manage the creation, deletion, and operation of ngrok tunnels, both HTTP and TCP, using the ngrok API. It provides a set of functions and a class to interact with ngrok's services, allowing users to reserve domains and TCP addresses, and manage these resources programmatically. The file includes functions to create and delete reserved domains and TCP addresses, leveraging the `httpx` library for HTTP requests to the ngrok API. Additionally, it includes a utility function to generate unique subdomain names based on developer input.

The core component of the file is the `TunnelManager` class, which orchestrates the lifecycle of ngrok tunnels. It uses asynchronous programming with the `asyncio` library to handle multiple tunnels concurrently. The class provides methods to start and stop tunnels, send messages to a server, and handle commands received from a FastAPI server. The `TunnelManager` class is designed to maintain a connection to a server, manage tunnel processes, and ensure that tunnels are started and stopped as needed. The file also includes a context manager for prefixed output, which modifies the standard output and error streams to include a specified prefix, aiding in logging and debugging. Overall, this code serves as a comprehensive tool for managing ngrok tunnels in an automated and scalable manner.
# Imports and Dependencies

---
- `asyncio`
- `re`
- `sys`
- `collections.abc`
- `contextlib`
- `typing`
- `httpx`
- `models`


# Global Variables

---
### NGROK_BASE_API_URL 
- **Type**: ``str``
- **Description**: `NGROK_BASE_API_URL` is a string variable that holds the base URL for the ngrok API, which is 'https://api.ngrok.com'. This URL is used as the foundational endpoint for making API requests to ngrok's services.
- **Use**: This variable is used to construct full API endpoint URLs for various ngrok operations, such as creating or deleting reserved domains and TCP addresses.


# Classes

---
### PrefixedStream 
- **Type**: `class`
- **Members**:
    - `original`: The original TextIO stream to which the prefixed output will be written.
    - `prefix`: The prefix string that will be added to each line of text written to the stream.
- **Description**: The `PrefixedStream` class is a utility for writing text to a given `TextIO` stream with a specified prefix added to each line. It is initialized with an original stream and a prefix string. The `write` method adds the prefix to non-empty lines before writing them to the original stream, while the `flush` and `fileno` methods delegate their operations to the original stream, ensuring compatibility with standard stream operations.

**Methods**

---
#### PrefixedStream.__init__
The `__init__` function initializes a `PrefixedStream` object with an original text stream and a prefix for output.
- **Inputs**:
    - `original`: A `TextIO` object representing the original text stream to be wrapped.
    - `prefix`: A string that will be prefixed to each line of output written to the stream.
- **Control Flow**:
    - Assigns the `original` parameter to the `self.original` attribute of the object.
    - Assigns the `prefix` parameter to the `self.prefix` attribute of the object.
- **Output**:
    - The function does not return any value; it initializes the object's attributes.


---
#### PrefixedStream.fileno
The `fileno` function returns the file descriptor of the original stream.
- **Inputs**:
    - `self`: An instance of the PrefixedStream class, which contains an original stream and a prefix.
- **Control Flow**:
    - The function directly calls and returns the result of the `fileno` method on the `original` attribute of the `self` object.
- **Output**:
    - An integer representing the file descriptor of the original stream.


---
#### PrefixedStream.flush
The `flush` function calls the `flush` method on the `original` stream to ensure all buffered data is written out.
- **Inputs**:
    - `self`: An instance of the `PrefixedStream` class, which contains an `original` stream and a `prefix` string.
- **Control Flow**:
    - The function directly calls the `flush` method on the `original` stream associated with the `PrefixedStream` instance.
- **Output**:
    - The function does not return any value; it performs an action to flush the stream.


---
#### PrefixedStream.write
The `write` function writes text to an original stream, prefixing it with a specified string if the text is not empty or whitespace.
- **Inputs**:
    - `text`: A string of text to be written to the original stream.
- **Control Flow**:
    - Check if the input text, when stripped of leading and trailing whitespace, is non-empty.
    - If the text is non-empty, write the text to the original stream prefixed with the specified prefix enclosed in square brackets.
    - If the text is empty or only whitespace, write the text to the original stream without any prefix.
- **Output**:
    - The function does not return any value; it writes to the original stream as a side effect.



---
### TunnelManager 
- **Type**: `class`
- **Members**:
    - `domains`: A list of NgrokReservedDomain objects representing the domains to be used for HTTP tunnels.
    - `http_ports`: A list of integers representing the HTTP ports corresponding to the domains.
    - `tcp_addresses`: A list of NgrokReservedTcpAddress objects representing the addresses for TCP tunnels.
    - `tcp_ports`: A list of integers representing the TCP ports corresponding to the TCP addresses.
    - `processes`: A dictionary mapping domain or address strings to their corresponding asyncio subprocesses.
    - `tasks`: A list of asyncio tasks for managing tunnel operations.
    - `reader`: An optional asyncio StreamReader for reading data from the server.
    - `writer`: An optional asyncio StreamWriter for sending data to the server.
    - `_connected`: An asyncio Event used to signal when a connection to the server is established.
- **Description**: The TunnelManager class is responsible for managing ngrok tunnels, both HTTP and TCP, by interfacing with a FastAPI server. It initializes with lists of domains, HTTP ports, TCP addresses, and TCP ports, ensuring that the number of domains matches the number of HTTP ports and the number of TCP addresses matches the number of TCP ports. The class provides methods to start and stop all tunnels, send messages to the server, handle server commands, and maintain the status of each tunnel. It uses asyncio for asynchronous operations, allowing it to manage multiple tunnels concurrently and handle server connections and commands efficiently.

**Methods**

---
#### TunnelManager.__init__
The `__init__` function initializes a `TunnelManager` instance with specified domains, HTTP ports, TCP addresses, and TCP ports, ensuring the counts of domains match HTTP ports and TCP addresses match TCP ports.
- **Inputs**:
    - `domains`: A list of `NgrokReservedDomain` objects representing the reserved domains for the tunnels.
    - `http_ports`: A list of integers representing the HTTP ports corresponding to each domain.
    - `tcp_addresses`: A list of `NgrokReservedTcpAddress` objects representing the reserved TCP addresses for the tunnels.
    - `tcp_ports`: A list of integers representing the TCP ports corresponding to each TCP address.
- **Control Flow**:
    - Check if the length of `domains` matches the length of `http_ports`; if not, raise a `ValueError`.
    - Check if the length of `tcp_addresses` matches the length of `tcp_ports`; if not, raise a `ValueError`.
    - Initialize instance variables `domains`, `http_ports`, `tcp_addresses`, and `tcp_ports` with the provided arguments.
    - Initialize `processes` as an empty dictionary to store subprocesses associated with each domain or TCP address.
    - Initialize `tasks` as an empty list to store asynchronous tasks for managing tunnels.
    - Initialize `reader` and `writer` as `None` to handle server communication streams.
    - Initialize `_connected` as an `asyncio.Event` to manage connection state with the server.
- **Output**:
    - The function does not return any value; it initializes the instance variables and validates input lengths.


---
#### TunnelManager.connect_to_server
The `connect_to_server` function establishes a persistent connection to a FastAPI server, listens for commands, and handles connection errors with retries.
- **Inputs**:
    - None
- **Control Flow**:
    - The function enters an infinite loop to continuously attempt connection to the server.
    - Within the loop, it tries to open a connection to 'localhost' on port 9000 using asyncio's `open_connection` method.
    - Upon successful connection, it sends a 'Connected to server' message and sets an internal event to signal connection status.
    - It enters another loop to read data from the server using `readline` from the reader stream.
    - If data is received, it decodes and checks if it starts with 'COMMAND:', then extracts and handles the command using `handle_command`.
    - If the connection is refused, it prints an error message and raises the exception.
    - For other exceptions, it prints the error, closes the writer if open, clears the connection event, and waits 5 seconds before retrying.
- **Output**:
    - The function does not return any value; it operates asynchronously to manage server connections and command handling.


---
#### TunnelManager.get_status
The `get_status` function asynchronously retrieves and sends the status of all active tunnels managed by the `TunnelManager` class.
- **Inputs**:
    - None
- **Control Flow**:
    - The function constructs a status message by iterating over the `self.processes` dictionary, which contains the active processes for each tunnel.
    - For each process, it checks if the `returncode` is `None` to determine if the process is still running, and appends the status ('running' or 'stopped') to the status message.
    - If there are no active processes, it defaults the status message to 'No active tunnels'.
    - The constructed status message is then sent using the `send_message` method.
- **Output**:
    - The function does not return any value; it sends the status message to a connected server or client.


---
#### TunnelManager.handle_command
The `handle_command` function processes server commands to manage ngrok tunnels by executing corresponding actions or sending an error message for unknown commands.
- **Inputs**:
    - `command`: A string representing the command received from the server, which can be 'status', 'stop', or 'start'.
- **Control Flow**:
    - A dictionary `commands` is defined, mapping command strings ('status', 'stop', 'start') to their respective handler methods (`get_status`, `stop_all_tunnels`, `start_all_tunnels`).
    - The function retrieves the handler function from the `commands` dictionary using the provided `command` string.
    - If a handler is found, it is awaited and executed asynchronously.
    - If no handler is found, an error message indicating an unknown command is sent to the server using `send_message`.
- **Output**:
    - The function does not return any value; it performs actions based on the command or sends a message to the server.


---
#### TunnelManager.run
The `run` function manages the lifecycle of a tunnel manager, handling server connections and tunnel operations asynchronously.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating an asynchronous task to connect to the server using `connect_to_server` and appends this task to the `tasks` list.
    - It waits for the server connection to be established by awaiting the `_connected` event.
    - Once connected, it starts all tunnels by calling `start_all_tunnels`.
    - It then gathers all tasks in the `tasks` list to run them concurrently using `asyncio.gather`.
    - If a `KeyboardInterrupt` is raised, it stops all tunnels by calling `stop_all_tunnels`.
    - In the `finally` block, it ensures that if a writer exists, it is closed and waits for it to be fully closed.
- **Output**:
    - The function does not return any value; it manages the asynchronous execution of server connections and tunnel operations.


---
#### TunnelManager.run_tcp_tunnel
The `run_tcp_tunnel` function asynchronously starts and manages a TCP ngrok tunnel for a specified address and port.
- **Inputs**:
    - `tcp_address`: An instance of NgrokReservedTcpAddress representing the reserved TCP address for the tunnel.
    - `port`: An integer representing the local port number to be tunneled.
- **Control Flow**:
    - The function waits for a server connection to be established by awaiting `self._connected.wait()`.
    - It constructs a command list `cmd` to start the ngrok TCP tunnel using the provided `tcp_address` and `port`.
    - An asynchronous subprocess is created to execute the ngrok command, capturing its output.
    - The process is stored in `self.processes` using the TCP address as the key.
    - A message is sent indicating the start of the TCP tunnel.
    - The function enters a loop to read lines from the subprocess's stdout, sending each line as a message prefixed with the TCP address.
    - If an exception occurs, an error message is sent.
    - Finally, the process is removed from `self.processes` in the `finally` block.
- **Output**:
    - The function does not return any value; it manages the lifecycle of a TCP ngrok tunnel and communicates status and output via messages.


---
#### TunnelManager.run_tunnel
The `run_tunnel` function asynchronously starts and manages an HTTP ngrok tunnel for a specified domain and port.
- **Inputs**:
    - `domain`: An instance of `NgrokReservedDomain` representing the domain for which the tunnel is to be created.
    - `port`: An integer representing the port number on which the tunnel will be established.
- **Control Flow**:
    - The function first waits for a server connection to be established by awaiting the `_connected` event.
    - It constructs a command to start an ngrok HTTP tunnel using the specified domain and port.
    - The command is executed asynchronously using `asyncio.create_subprocess_exec`, capturing the process's stdout and stderr.
    - The process is stored in the `processes` dictionary with the domain as the key.
    - A message is sent indicating the tunnel has started.
    - The function enters a loop to read lines from the process's stdout, decoding and sending each line as a message prefixed with the domain name.
    - If an exception occurs during this process, an error message is sent.
    - Finally, the process is removed from the `processes` dictionary in a `finally` block to ensure cleanup.
- **Output**:
    - The function does not return any value; it performs its operations asynchronously and communicates via messages.


---
#### TunnelManager.send_message
The `send_message` function asynchronously sends a message to a server using a stream writer.
- **Inputs**:
    - `message`: A string representing the message to be sent to the server.
- **Control Flow**:
    - Check if the `writer` attribute is not `None` to ensure a connection is available.
    - Attempt to write the message, followed by a newline character, to the writer stream and encode it to bytes.
    - Await the `drain` method on the writer to ensure the message is sent.
    - Catch any exceptions that occur during the write or drain process and print an error message.
- **Output**:
    - The function does not return any value; it performs an asynchronous operation to send a message.


---
#### TunnelManager.start_all_tunnels
The `start_all_tunnels` function initiates all HTTP and TCP tunnels that are not already running.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over pairs of domains and HTTP ports, checking if each domain is not already in the `processes` dictionary.
    - For each domain not in `processes`, it creates an asynchronous task to run an HTTP tunnel using the `run_tunnel` method and appends it to the `tasks` list.
    - Iterates over pairs of TCP addresses and TCP ports, checking if each address is not already in the `processes` dictionary.
    - For each TCP address not in `processes`, it creates an asynchronous task to run a TCP tunnel using the `run_tcp_tunnel` method and appends it to the `tasks` list.
- **Output**:
    - The function does not return any value; it modifies the `tasks` list by adding tasks to start tunnels.


---
#### TunnelManager.stop_all_tunnels
The `stop_all_tunnels` function terminates all active tunnel processes and clears the process list.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over all processes stored in `self.processes` and calls `terminate()` on each to stop them.
    - Uses `asyncio.gather` to wait for all processes to finish terminating by calling `wait()` on each process.
    - Clears the `self.processes` dictionary to remove all references to the terminated processes.
    - Sends a message 'All tunnels stopped' using the `send_message` method.
- **Output**:
    - The function does not return any value (returns `None`).



# Functions

---
### create_reserved_domain 
The `create_reserved_domain` function creates a reserved domain on the ngrok platform using the provided API key, subdomain, description, and optional region.
- **Inputs**:
    - `api_key`: A string representing the API key used for authentication with the ngrok API.
    - `subdomain`: A string representing the desired subdomain to reserve on ngrok.
    - `description`: A string providing a description for the reserved domain.
    - `region`: An optional string specifying the region for the reserved domain, defaulting to 'us'.
- **Control Flow**:
    - Constructs the full domain name by appending '.ngrok.io' to the subdomain.
    - Sets up the request headers with authorization, content type, and ngrok version.
    - Prepares the request payload with the full domain, region, and description.
    - Sends a POST request to the ngrok API to create the reserved domain.
    - Checks the response status code: if 201, prints success message and returns the response JSON; if 409, prints a warning about the domain being taken and returns the response JSON; otherwise, prints an error message and raises an exception.
- **Output**:
    - Returns a dictionary containing the JSON response from the ngrok API if the domain is successfully created or already taken.


---
### create_reserved_tcp_address 
The function `create_reserved_tcp_address` creates a reserved TCP address using the ngrok API and returns an `NgrokReservedTcpAddress` object if successful.
- **Inputs**:
    - `api_key`: A string representing the API key used for authentication with the ngrok API.
    - `description`: A string providing a description for the reserved TCP address.
    - `region`: An optional string specifying the region for the reserved TCP address, defaulting to 'us'.
    - `metadata`: An optional string or None, providing additional metadata for the reserved TCP address.
- **Control Flow**:
    - Constructs the ngrok API URL for creating reserved addresses.
    - Sets up the headers for the HTTP request, including authorization using the provided API key.
    - Prepares the data payload with the description and region, adding metadata if provided.
    - Sends a POST request to the ngrok API to create the reserved TCP address.
    - Checks the response status code; if 201, it indicates success, and the function prints a success message and returns an `NgrokReservedTcpAddress` object.
    - If the response status code is not 201, it prints an error message and raises an exception using `response.raise_for_status()`.
- **Output**:
    - Returns an `NgrokReservedTcpAddress` object containing the address, description, region, status, and metadata if the creation is successful; otherwise, raises an HTTP error.


---
### delete_reserved_domain 
The `delete_reserved_domain` function attempts to delete a reserved domain from the ngrok service using the provided API key and domain ID.
- **Inputs**:
    - `api_key`: A string representing the API key used for authentication with the ngrok API.
    - `domain_id`: A string representing the unique identifier of the reserved domain to be deleted.
- **Control Flow**:
    - Construct the ngrok API URL for the reserved domain using the base URL and the provided domain ID.
    - Set up the request headers with the authorization token and ngrok version.
    - Attempt to send a DELETE request to the constructed URL with the specified headers.
    - Check the response status code: if it is 204, print a success message and return True; otherwise, print a failure message with the status code and return False.
    - If an exception occurs during the request, catch it, print an error message, and return False.
- **Output**:
    - A boolean value indicating whether the reserved domain was successfully deleted (True) or not (False).


---
### delete_reserved_tcp_address 
The `delete_reserved_tcp_address` function deletes a reserved TCP address from the ngrok service using the provided API key and address ID.
- **Inputs**:
    - `api_key`: A string representing the API key used for authentication with the ngrok API.
    - `address_id`: A string representing the ID of the reserved TCP address to be deleted.
- **Control Flow**:
    - Constructs the ngrok API URL for the reserved TCP address using the base URL and the provided address ID.
    - Sets up the headers for the HTTP request, including the authorization token and ngrok version.
    - Attempts to send a DELETE request to the ngrok API to delete the reserved TCP address.
    - Checks the response status code: if it is 204, prints a success message and returns True; otherwise, prints a failure message with the status code and returns False.
    - Catches any exceptions during the request and prints an error message, returning False.
- **Output**:
    - Returns a boolean indicating whether the deletion was successful (True) or not (False).


---
### generate_unique_subdomain 
The `generate_unique_subdomain` function creates a sanitized and formatted subdomain string using a developer's name and an optional prefix.
- **Inputs**:
    - `developer_name`: A string representing the developer's name, which will be sanitized and used as part of the subdomain.
    - `prefix`: An optional string prefix for the subdomain, defaulting to 'app', which will also be sanitized.
    - `suffix_length`: An optional integer specifying the length of a suffix, defaulting to 4, though it is not used in the function.
- **Control Flow**:
    - Sanitize the `developer_name` by converting it to lowercase, replacing spaces with hyphens, and removing any characters that are not lowercase letters, numbers, or hyphens.
    - Sanitize the `prefix` in the same manner as the `developer_name`.
    - Concatenate the sanitized `developer_name` and `prefix` with a hyphen in between to form the subdomain string.
- **Output**:
    - A string representing the sanitized and formatted subdomain.


---
### prefixed_output 
The `prefixed_output` function temporarily redirects standard output and error streams to include a specified prefix for each line of output.
- **Inputs**:
    - `prefix`: A string that will be prefixed to each line of output written to the standard output and error streams.
- **Control Flow**:
    - The function saves the original `sys.stdout` and `sys.stderr` to restore them later.
    - A nested class `PrefixedStream` is defined to wrap an original stream and prepend a prefix to each line of text written to it.
    - Instances of `PrefixedStream` are created for both `sys.stdout` and `sys.stderr`, using the provided prefix.
    - The global `sys.stdout` and `sys.stderr` are replaced with these `PrefixedStream` instances.
    - The function yields control back to the caller, allowing the caller to execute code with the prefixed output streams.
    - In the `finally` block, the original `sys.stdout` and `sys.stderr` are restored, ensuring that the redirection is only temporary.
- **Output**:
    - The function yields control to the caller, allowing them to execute code with the modified output streams, and does not return any value.


---
### run_ngrok_tunnels 
The `run_ngrok_tunnels` function initializes and runs ngrok tunnels for specified domains and TCP addresses using a TunnelManager.
- **Inputs**:
    - `domains`: A list of NgrokReservedDomain objects representing the domains for which HTTP tunnels will be created.
    - `http_ports`: A list of integers representing the HTTP ports corresponding to each domain.
    - `tcp_addresses`: A list of NgrokReservedTcpAddress objects representing the TCP addresses for which TCP tunnels will be created.
    - `tcp_ports`: A list of integers representing the TCP ports corresponding to each TCP address.
- **Control Flow**:
    - The function creates an instance of TunnelManager with the provided domains, HTTP ports, TCP addresses, and TCP ports.
    - It then calls the `run` method of the TunnelManager instance, which manages the lifecycle of the ngrok tunnels, including connecting to a server, starting, and stopping tunnels.
- **Output**:
    - The function does not return any value; it performs its operations asynchronously and manages ngrok tunnels.


