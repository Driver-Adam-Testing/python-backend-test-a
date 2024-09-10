import openai
from openai import OpenAI

from shared.agent.base import AgentBase


class OpenAIStrictAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        tools = kwargs.get("tools", [])
        for i, tool in enumerate(tools):
            tools[i] = openai.pydantic_function_tool(tool)
        kwargs["tools"] = tools
        self.client = OpenAI()
        super().__init__(*args, **kwargs)

    def _execute_tool_calls(self, tool_calls):
        """
        OpenAI expects all tool calls to return in a several tool messages with tool_call_id.
        """
        for tc in tool_calls:
            message = {
                "tool_call_id": tc.id,
                "role": "tool",
                "name": tc.function.name,
                "content": "Error in tool call",
            }

            try:
                message["content"] = tc.function.parsed_arguments.execute(self)
            except Exception as e:
                message["content"] = f"Error: {e}"
            self.add_message(message)

    def _create_completion(self):
        completion_kwargs = {}
        completion_kwargs["model"] = self.model
        completion_kwargs["messages"] = self.messages
        if self.tools and self.max_iterations > 1:
            completion_kwargs["tools"] = self.tools
            completion_kwargs["tool_choice"] = "auto"
        if self.response_format:
            completion_kwargs["response_format"] = self.response_format
        return self.client.beta.chat.completions.parse(**completion_kwargs)

    def _execute_iteration(self) -> str | None:
        response = self._create_completion()
        self.add_message(response.choices[0].message)
        if response.choices[0].message.tool_calls:
            self._execute_tool_calls(response.choices[0].message.tool_calls)
        else:
            return response.choices[0].message.content
