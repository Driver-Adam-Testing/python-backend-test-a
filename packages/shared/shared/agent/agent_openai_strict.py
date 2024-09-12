from concurrent.futures import ThreadPoolExecutor, as_completed

import openai
from openai import OpenAI

from shared.agent.agent_base import AgentBase


class OpenAIStrictAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        tools = [
            openai.pydantic_function_tool(tool) for tool in kwargs.get("tools", [])
        ]
        kwargs["tools"] = tools
        self.client = OpenAI()
        super().__init__(*args, **kwargs)

    def _execute_tool_calls(self, tool_calls):
        # TODO: set tools to have an optional token limit for the results. This should be context_window / len(tool_calls) / max_iterations
        """
        OpenAI expects all tool calls to return in several tool messages with tool_call_id.
        """

        def execute_tool_call(tc):
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
            return message

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(execute_tool_call, tc) for tc in tool_calls]
            for future in as_completed(futures):
                self.add_message(future.result())

    def _execute_iteration(self) -> str | None:
        completion_kwargs = {
            "model": self.model,
            "messages": self.messages,
        }
        if (
            self.tools
            and self.max_iterations > 1
            and self.iteration < self.max_iterations
        ):
            completion_kwargs.update(
                {
                    "tools": self.tools,
                    "tool_choice": "auto",
                }
            )
        if self.response_format:
            completion_kwargs["response_format"] = self.response_format
        try:
            response = self.client.beta.chat.completions.parse(**completion_kwargs)
        except Exception as e:
            if self.iteration < self.max_iterations:
                # NOTE: it's ok to list the error and return None if there are more iterations for the LLM to respond.
                self.add_message(str(e))
                return None
            raise e
        self.add_message(response.choices[0].message)

        if response.choices[0].message.tool_calls:
            self._execute_tool_calls(response.choices[0].message.tool_calls)
        else:
            return response.choices[0].message.content
