import json

from anthropic import Anthropic

from shared.agent.base import AgentBase


class AnthropicStrictAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        response_format = kwargs.pop("response_format", None)
        self.response_format = response_format
        self.client = Anthropic()
        super().__init__(*args, **kwargs)

    def _execute_tool_calls(self, tool_calls):
        """
        Anthropic expects all tool calls to return in a single user message with several contents.
        """
        message = {"role": "user", "content": []}

        for tc in tool_calls:
            tool_message = {
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": "Error in tool call",
            }

            try:
                tool = next(tool for tool in self.tools if tool.name == tc["name"])
                tool_message["content"] = tool(**tc["input"]).execute(self)
            except Exception as e:
                tool_message["content"] = f"Error: {e}"

            message["content"].append(tool_message)

        self.add_message(message)

    def _create_completion(self):
        completion_kwargs = {}
        completion_kwargs["model"] = self.model
        completion_kwargs["messages"] = self.messages
        completion_kwargs["max_tokens"] = 2048
        if self.tools:
            print(self.tools)
            completion_kwargs["tools"] = [
                tool.anthropic_tool_schema() for tool in self.tools
            ]
            completion_kwargs["tool_choice"] = "auto"
        system_messages = " ".join(
            message["content"]
            for message in self.messages
            if message["role"] == "system"
        )
        completion_kwargs["system"] = system_messages
        print(completion_kwargs)
        response = self.client.messages.create(**completion_kwargs)
        return response

    def _increment_iterator(self):
        super()._increment_iterator()
        response = self._create_completion()
        self.add_message(response.choices[0].message)

        tool_calls = []
        for content in response.choices[0].message["content"]:
            if content["type"] == "tool_use":
                tool_call = {
                    "id": content["id"],
                    "name": content["name"],
                    "input": content["input"],
                }
                tool_calls.append(tool_call)

        if tool_calls:
            self._execute_tool_calls(tool_calls)
            return True

        return False

    def invoke(self, prompt: str):
        response = super().invoke(prompt)
        if self.response_format:
            format_prompt = f"Please format the following response into the specified format: {self.response_format.schema_json()}\nResponse: {response}"
            format_response = (
                self.client.completions.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": format_prompt},
                        {"role": "assistant", "content": "{"},
                    ],
                )
                .content[0]
                .text
            )
            formatted_response = json.loads(
                "{" + format_response[: format_response.rfind("}") + 1]
            )
            return self.response_format.parse_obj(formatted_response)
        return response
