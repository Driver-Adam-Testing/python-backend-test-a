from fastmcp import FastMCP

my_mcp = FastMCP(
    "Driver MCP Server",
    instructions="This is a demo Driver MCP Server",
    stateless_http=True,
)


@my_mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@my_mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
