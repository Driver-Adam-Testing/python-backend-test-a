from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from shared.agent.base import AgentBase
from shared.agent.models.claude import helpers


class AnthropicAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = anthropic.Anthropic()

    def _execute_tool_calls(self, tool_calls):
        """
        Anthropic expects all tool calls to return in a single user message.
        """
        if not tool_calls:
            return
        futures = []

        with ThreadPoolExecutor() as executor:
            for tool_call in tool_calls:
                future = executor.submit(self._execute_tool_call, tool_call)
                futures.append(future)

            tool_names = []
            tool_call_ids = []
            function_responses = []

            for future in as_completed(futures):
                function_response, tool_call_id, function_name = future.result()
                tool_names.append(function_name)
                tool_call_ids.append(tool_call_id)
                function_responses.append(function_response)

            formatted_tool_results = helpers.format_tool_results(
                tool_names, tool_call_ids, function_responses
            )
            self.add_message(
                {
                    "role": "user",
                    "content": formatted_tool_results,
                }
            )

    def _create_completion(self):
        """
        Anthropic only takes a single system prompt, so aggregate all of them.
        """
        system_messages = [
            message["content"]
            for message in self.messages
            if message["role"] == "system"
        ]
        system_string = " ".join(system_messages)
        filtered_messages = [
            message
            for message in self.messages
            if message["role"] in ["user", "assistant"]
        ]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_string,
            messages=filtered_messages,
        )
        return response

    def _iterate(self):
        super()._iterate()
        user_messages = []
        for message in reversed(self.messages):
            if message["role"] == "user":
                user_messages.append(message["content"])
                self.messages.pop()
            else:
                break
        merged_user_message = " ".join(user_messages)
        self.messages.append({"role": "user", "content": merged_user_message})
        response = self._create_completion()
        self.add_message({"role": "assistant", "content": response.content[0].text})
        tool_calls = helpers.parse_tool_calls_from_response(response.content[0].text)
        if tool_calls:
            self._execute_tool_calls(tool_calls)
            return True
        else:
            return False

    def invoke(self, prompt: str):
        if self.iteration == 0 and self.tools:
            self.add_message(
                {
                    "role": "system",
                    "content": helpers.format_tool_prompt(self.tools),
                }
            )
        return super().invoke(prompt)
