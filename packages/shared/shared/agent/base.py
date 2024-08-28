import json
import uuid

from database.db import get_session
from database.models_v1 import RuntimeLogAgentInstance, RuntimeLogAgentMessage
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from shared.utils.bcolors import print_dict


class AgentBase:
    def __init__(
        self,
        organization_id: str,
        model: str,
        paths: list[str] | None = None,
        max_iterations: int = 1,
        tools=None,
        agent_id: uuid.UUID | None = None,
        log: bool = True,
        debug: bool = True,
    ):
        self.organization_id = organization_id
        self.model = model
        self.log = log
        self.debug = debug
        self.agent_id = agent_id
        self.paths = paths if paths is not None else ["/"]
        self.tools = tools if tools is not None else []
        self.max_iterations = max_iterations
        self.iteration = 0
        self.messages = []
        self.search_results = []
        self._load_or_initialize()

    def _load_or_initialize(self):
        if self.log:
            if self.agent_id is None:
                with get_session() as session:
                    agent_instance = RuntimeLogAgentInstance(
                        workspace_id=None,
                        codebase_id=None,
                        model=self.model,
                        organization_id=self.organization_id,
                    )
                    session.add(agent_instance)
                    session.commit()
                    session.refresh(agent_instance)
                    self.agent_id = agent_instance.id
            else:
                with get_session() as session:
                    agent_instance = session.get(RuntimeLogAgentInstance, self.agent_id)
                    if agent_instance:
                        for message in agent_instance.messages:
                            self.add_message(message.message)

    def add_search_results(self, results):
        self.search_results.append(results)

    def _print_message(self, message: ChatCompletionMessage | dict[str, str]):
        try:
            if not isinstance(message, dict):
                if hasattr(message, "to_dict") and callable(message.to_dict):
                    message = message.to_dict()
                else:
                    message = {
                        attr: getattr(message, attr)
                        for attr in dir(message)
                        if not attr.startswith("_")
                        and not callable(getattr(message, attr))
                    }
            print_dict(message)
        except Exception as e:
            print(f"Could not print {e}")

    def add_message(self, message: ChatCompletionMessage | dict[str, str] | str):
        if isinstance(message, ChatCompletionMessage):
            self.messages.append(message)
        elif isinstance(message, str):
            message = {"role": "user", "content": message}
        else:
            self.messages.append(message)
        if self.debug:
            self._print_message(message)
        if self.log:
            self._log_agent_message(message)

    def _log_agent_message(self, message: ChatCompletionMessage | dict[str, str]):
        if isinstance(message, ChatCompletionMessage):
            log_message = RuntimeLogAgentMessage(
                agent_instance_id=self.agent_id, message=message.model_dump()
            )
        else:
            log_message = RuntimeLogAgentMessage(
                agent_instance_id=self.agent_id, message=message
            )
        with get_session() as session:
            session.add(log_message)
            session.commit()
            session.refresh(log_message)

    def _execute_tool_call(self, tool_call):
        # TODO: there's probably a better  hierarchical version of determining whether the tool was correctly called.
        function_id = getattr(tool_call, "id", None)
        if not hasattr(tool_call, "function"):
            return (
                "Error: 'tool_call' does not have 'function' attribute.",
                function_id,
                None,
            )
        function_name = getattr(tool_call.function, "name", None)
        function_arguments = getattr(tool_call.function, "arguments", None)

        if not function_name or not function_arguments or not function_id:
            return (
                "Error: Invalid tool call structure. Expected 'name', 'arguments', and 'id'.",
                function_id,
                function_name,
            )

        try:
            function = next(
                tool.function for tool in self.tools if tool.name == function_name
            )
            if self.debug:
                print_dict(
                    {
                        "function_name": function_name,
                        "function_arguments": function_arguments,
                    }
                )

            if isinstance(function_arguments, str):
                function_args = json.loads(function_arguments)
            elif isinstance(function_arguments, dict):
                function_args = function_arguments
            else:
                raise TypeError("Arguments must be either a string or a dictionary.")
            if "agent_context" in function.__code__.co_varnames:
                if function_args is None:
                    function_args = {}
                function_args["agent_context"] = self
            return (function(**function_args), function_id, function_name)
        except Exception as e:
            return (f"Error: {str(e)}", function_id, function_name)

    def _iterate(self):
        self.iteration += 1
        if self.max_iterations > 1:
            self.add_message(
                {
                    "role": "user",
                    "content": f"There are {self.max_iterations - self.iteration} remaining AI agent iterations remaining to solve the problem.",
                }
            )

    def invoke(self, prompt: str):
        self.iteration = 0
        self.add_message({"role": "user", "content": prompt})
        while self._iterate():
            if self.iteration > self.max_iterations:
                break
        try:
            return self.messages[-1].content
        except Exception:
            return self.messages[-1]["content"]
