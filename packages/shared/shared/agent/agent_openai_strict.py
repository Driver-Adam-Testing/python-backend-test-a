from concurrent.futures import ThreadPoolExecutor, as_completed

import openai
from openai import OpenAI

from shared.agent.agent_base import AgentBase
from shared.agent.tools.tool_strict import ToolStrict


class OpenAIStrictAgent(AgentBase):
    def __init__(
        self, tools: list[ToolStrict] | None = None, *args: any, **kwargs: any
    ) -> None:
        if tools is None:
            tools = []
        processed_tools = [openai.pydantic_function_tool(tool) for tool in tools]
        kwargs["tools"] = processed_tools
        self.client = OpenAI()
        super().__init__(*args, **kwargs)

        for tool in tools:
            if hasattr(tool, "system_prompt") and callable(tool.system_prompt):
                self.add_message({"role": "system", "content": tool.system_prompt()})

    def _execute_tool_calls(self, tool_calls: any) -> None:
        """
        OpenAI expects all tool calls to return in several tool messages with tool_call_id.
        """

        # TODO: set tools to have an optional token limit for the results. This should be context_window / len(tool_calls) / max_iterations
        def execute_tool_call(tc: any) -> dict:
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

    def _generate_response(self, completion_kwargs: dict) -> openai.ChatCompletion:
        response = self.client.beta.chat.completions.parse(**completion_kwargs)

        # if self.llm_usage_session:
        #     usage_metric = self.llm_usage_session.compute_usage(
        #         prompts=[str(completion_kwargs.get("messages", ""))],
        #         response=response,
        #         event_type=UsageEventType.AGENT_PIPELINE_USAGE_DEBIT,
        #         model=self.model,
        #         provider="OpenAI",
        #     )
        #     self.llm_usage_session.send_event(usage_metric)

        return response

    def _execute_iteration(self) -> str | None:
        if self.model_config.system_prompts == "none":
            adjusted_messages = [
                {**msg, "role": "user"} if msg.get("role") == "system" else msg
                for msg in self.messages
            ]
        else:
            adjusted_messages = self.messages

        completion_kwargs = {
            "model": self.model,
            "messages": adjusted_messages,
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
            response = self._generate_response(completion_kwargs=completion_kwargs)
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
