import json
import uuid
from abc import ABC, abstractmethod

from database.db import get_session
from database.models_v1 import RuntimeLogAgentInstance, RuntimeLogAgentMessage

from shared.agent.tools.tool_strict import ToolStrict
from shared.utils.bcolors import print_dict


class AgentBase(ABC):
    def __init__(
        self,
        organization_id: str,
        model: str,
        paths: list[str] | None = None,
        max_iterations: int = 1,
        tools: list[ToolStrict] | None = None,
        agent_id: uuid.UUID | None = None,
        response_format: type | None = None,
        log: bool = False,
        debug: bool = True,
    ):
        # NOTE: After the migration is deployed, change this to be an input
        self.log = log
        self.organization_id = organization_id
        self.model = model
        self.debug = debug
        self.agent_id = agent_id
        self.paths = paths if paths is not None else []
        self.tools = tools if tools is not None else []
        self.max_iterations = max_iterations
        self.iteration = 0
        self.messages = []
        self.search_results = []
        self.response_format = response_format
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

    def _increment_iterator_message(self) -> bool:
        if self.max_iterations > 1:
            self.add_message(
                {
                    "role": "user",
                    "content": f"There are {self.max_iterations - self.iteration} remaining AI agent iterations remaining to solve the problem.",
                }
            )
        self.iteration += 1
        return self.iteration <= self.max_iterations

    @abstractmethod
    def _execute_iteration(self) -> str | None:
        pass

    def invoke(self, prompt: str = None):
        self.iteration = 0
        if prompt is not None:
            self.add_message({"role": "user", "content": prompt})
        while self._increment_iterator_message():
            response = self._execute_iteration()
            if response is not None:
                if self.response_format is not None:
                    return self.response_format(**json.loads(response))
                else:
                    return response
        raise RuntimeError(
            "Agent failed to produce a valid response within the allowed iterations."
        )
