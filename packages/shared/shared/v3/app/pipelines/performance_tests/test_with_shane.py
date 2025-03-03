from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.llms.clients.llm_client import LlmClient


class TestWithShaneResponse(LlmResponseType):
    """
    This is a response type that is used to test the with shane pipeline.
    """

    shanes_thoughts: str
    shanes_action: str


clients = [
    LlmClient.claude_sonnet_3_7(),
]


def test_with_shane() -> None:
    for client in clients:
        response = client.single_shot(
            prompt="Hello, how are you?, make up some thoughts and actions!",
        )
        response.to_console()


if __name__ == "__main__":
    test_with_shane()
