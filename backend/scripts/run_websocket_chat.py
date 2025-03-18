import asyncio
import json

AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjBzU0lhMGozbU9YTXh4YUZuWnB5ZyJ9.eyJvcmdJZCI6Im9yZ19zNzZwVTF2OExBWWhUT1dCIiwib3JnX2Rpc3BsYXlfbmFtZSI6IkRyaXZlciBEZXZlbG9wZXJzIiwidXNlcklkIjoiYXV0aDB8NjY1MGU0YTBlNjBmZjE1N2Q0MzdiYWYzIiwidXNlcl9lbWFpbCI6Im5laWwuenVtd2FsZGUrZGV2QGRyaXZlcmFpLmNvbSIsInVzZXJfZnVsbF9uYW1lIjoiTmVpbCBadW13YWxkZSIsImlzcyI6Imh0dHBzOi8vYXV0aC5kZXYuZHJpdmVyYWkuY29tLyIsInN1YiI6ImF1dGgwfDY2NTBlNGEwZTYwZmYxNTdkNDM3YmFmMyIsImF1ZCI6WyJodHRwczovL2FwaS5kZXYuZHJpdmVyYWkuY29tL2FwaS92MSIsImh0dHBzOi8vZHJpdmVyYWktZGV2LnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3NDEzODEzOTQsImV4cCI6MTc0MTQ2Nzc5NCwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsIm9yZ19pZCI6Im9yZ19zNzZwVTF2OExBWWhUT1dCIiwib3JnX25hbWUiOiJkcml2ZXIiLCJhenAiOiJKQzMyMnNGTUczdFYzSGVQaEpqdHZEelJzbkgxMkFzSSIsInBlcm1pc3Npb25zIjpbImNvbnRlbnQ6ZWRpdG9yIiwiY29udGVudDpyZWFkb25seSIsIm9yZ2FuaXphdGlvbjptYW5hZ2VtZW50Il19.E14JBSg6inrRJKstD2wAtZCoXTyKwzAA3eRlnXqVZtmgCp-0bPv8y2Y8F_BLkz1-7nFUcuUu7jQoMiLZ2gcpa9-G9j2h44ZX4ZovdcKhh4d_o-cVENuBkXxwYKPjvp1KQ37BS1qa31PTmdLoLNnh1tY4h8WB07UWjZXK8ln6w0xuKMfPK231j7lBeCIsLl1amWEvHE6eUsJM99BTAOnC-8Ni_iV5Q0DMLt74SfOv72rmqeQRGT9gX-warNI9D8c79wMULfP3BgdT9PJRQX6PrSl3HA5TlWqsAgah1M8Y-9uJnNRsqNdLVVektKnrP58a3BqHDNTH5vcl9kGxzrHwFA"
NODE_IDS = ["42038e91-901c-4964-a1ee-cc273e6dae50"]

KEEP_ALIVE_INTERVAL = 30


async def send_keep_alive(websocket):
    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)
        try:
            await websocket.send("KEEP_ALIVE")
        except Exception as e:
            print(f"Error sending KEEP_ALIVE: {e}")
            break


async def run_websocket_chat():
    if AUTH_TOKEN:
        token = AUTH_TOKEN
    else:
        token = input("Please enter your auth token: ").strip()
    if not token:
        print("No token provided. Exiting...")
        return

    # Adjust if your server is running at a different host/port
    uri = "ws://localhost:8888/api/v1/chat/websocket"
    print(f"Connecting to {uri} with provided token...")

    # If an Authorization header is needed, pass extra_headers. Otherwise, adapt as necessary.
    try:
        import websockets
    except ImportError:
        print("The 'websockets' library is required to run this script but not found.")
        return
    async with websockets.connect(
        uri, additional_headers={"Authorization": f"Bearer {token}"}
    ) as websocket:
        print("Connected to chat endpoint. Sending setup message...")

        # Start the KEEP_ALIVE task
        keep_alive_task = asyncio.create_task(send_keep_alive(websocket))

        # Send the setup message with user input
        setup_message = json.dumps({"node_ids": NODE_IDS})
        await websocket.send(setup_message)
        try:
            while True:
                user_input = input("You: ")
                if user_input == "":
                    break
                await websocket.send(user_input)
                while True:
                    response = await websocket.recv()
                    if not response.startswith("GENERATION_COMPLETE"):
                        print(f"{response}", end="", flush=True)
                    else:
                        print("")
                        break
        except websockets.ConnectionClosed:
            print("Connection closed by server.")
        finally:
            keep_alive_task.cancel()


def main():
    asyncio.run(run_websocket_chat())


if __name__ == "__main__":
    main()
