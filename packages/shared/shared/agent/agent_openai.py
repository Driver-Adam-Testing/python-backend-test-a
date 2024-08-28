from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from shared.agent.base import AgentBase
from shared.agent.tools.tool_call import ToolCall


class OpenAIAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = OpenAI()

    @property
    def _tool_list(self):
        return [tool.to_open_ai_dict() for tool in self.tools]

    def _execute_tool_calls(self, tool_calls):
        """
        OpenAI expects all tool calls to return in a several tool messages with tool_call_id.
        """
        if not tool_calls:
            return
        futures = []

        with ThreadPoolExecutor() as executor:
            messages = []
            for tc in tool_calls:
                tool_call = ToolCall.from_openai_tool_call(tc)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.name,
                        "content": "Error in tool call",
                    }
                )
                future = executor.submit(self._execute_tool_call, tool_call)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    tool_call = future.result()
                    if tool_call.response:
                        message = next(
                            (
                                msg
                                for msg in messages
                                if msg["tool_call_id"] == tool_call.id
                            ),
                            None,
                        )
                        if message:
                            message["content"] = str(tool_call.response)
                except Exception:
                    pass
            for message in messages:
                self.add_message(message)

    def _create_completion(self):
        if self.tools:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._tool_list,
                tool_choice="auto",
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
        return response

    def _iterate(self):
        super()._iterate()
        response = self._create_completion()
        self.add_message(response.choices[0].message)
        if response.choices[0].message.tool_calls:
            self._execute_tool_calls(response.choices[0].message.tool_calls)
            return True
        else:
            return False

    def invoke(self, prompt: str):
        return super().invoke(prompt)
