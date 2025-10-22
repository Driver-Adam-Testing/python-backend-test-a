class ToolUseError(Exception):
    """
    Exception raised when an LLM agent provides invalid input or misuses a tool.

    The 'agent_message' should be returned to the LLM agent.
    """

    def __init__(self, agent_message: str, error_details: str | None = None) -> None:
        self.agent_message = agent_message
        super().__init__(self.agent_message)
