import uuid

from database.db import get_session
from database.models_v1 import RuntimeLogAgentInstance, RuntimeLogAgentMessage

from shared.agent.tools.tool_call import ToolCall
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

    def add_message(self, message: any):
        if isinstance(message, str):
            message = {"role": "user", "content": message}
        elif hasattr(message, "to_dict") and callable(message.to_dict):
            message = message.to_dict()
        elif isinstance(dict, str):
            pass
        self.messages.append(message)
        if self.debug:
            self._print_agent_message(message)
        if self.log:
            self._log_agent_message(message)

    def _print_agent_message(self, message: any):
        print_dict(message)

    def _log_agent_message(self, message: any):
        log_message = RuntimeLogAgentMessage(
            agent_instance_id=self.agent_id, message=message
        )
        with get_session() as session:
            session.add(log_message)
            session.commit()
            session.refresh(log_message)

    def _execute_tool_call(self, tool_call: ToolCall):
        try:
            function_to_execute = next(
                tool.function for tool in self.tools if tool.name == tool_call.name
            )
            execution_kwargs = tool_call.args
            if "agent_context" in function_to_execute.__code__.co_varnames:
                execution_kwargs["agent_context"] = self
            tool_call.response = function_to_execute(**execution_kwargs)
        except Exception as e:
            tool_call.response = f"Error: {str(e)}"
        return tool_call

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
