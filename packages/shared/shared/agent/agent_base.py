import json
import uuid
from abc import ABC, abstractmethod

from database.db import get_session
from database.models_v1 import RuntimeLogAgentInstance, RuntimeLogAgentMessage
from pydantic import BaseModel

from shared.agent.models.llm_models import ModelConfig
from shared.interfaces.agents.data_scope import DataScope
from shared.prompts.interface.iterations import (
    PROMPT_FINAL_ITERATION,
    PROMPT_FIRST_ITERATION,
    PROMPT_MIDDLE_ITERATION,
)
from shared.usage.llm_session import LLMUsageSession
from shared.utils.bcolors import print_dict


# ToolStrict Import for typing caused a circular import when calling modal. apparently tools.__init__.py gets called? why isn't this failing elsewhere.
class AgentBase(ABC):
    def __init__(
        self,
        model: str,
        scope: DataScope,
        tools: list[any] | None = None,
        max_iterations: int = 1,
        agent_id: uuid.UUID | None = None,
        response_format: type | None = None,
        log: bool = True,
        debug: bool = True,
        llm_usage_session: LLMUsageSession | None = None,
    ) -> None:
        # TODO: add ModelConfig (to get model metadata during execution)
        # TODO: Turn on logging

        self.log = log
        self.scope = scope
        self.model = model
        self.debug = debug
        self.agent_id = agent_id
        self.tools = tools if tools is not None else []
        self.max_iterations = max_iterations
        self.iteration = 0
        self.messages = []
        self.search_results = []
        self.response_format = response_format
        self.llm_usage_session = llm_usage_session

        if self.agent_id is not None:
            with get_session() as session:
                agent_instance = session.get(RuntimeLogAgentInstance, self.agent_id)
                if agent_instance:
                    for message in agent_instance.messages:
                        self.add_message(message.message)
        else:
            if self.log:
                with get_session() as session:
                    agent_instance = RuntimeLogAgentInstance(
                        model=self.model,
                        organization_id=self.scope.organization_id,
                    )
                    session.add(agent_instance)
                    session.commit()
                    session.refresh(agent_instance)
                    self.agent_id = agent_instance.id

    @property
    def model_config(self) -> ModelConfig:
        return ModelConfig.from_name(self.model)

    def add_search_results(self, results: any) -> None:
        self.search_results.append(results)

    def add_message(self, message: any) -> None:
        if isinstance(message, str):
            message = {"role": "user", "content": message}
        elif hasattr(message, "to_dict") and callable(message.to_dict):
            message = message.to_dict()
        self.messages.append(message)
        if self.debug:
            self._print_agent_message(message)

    def _print_agent_message(self, message: any) -> None:
        print_dict(message)

    def _increment_iterator_message(self) -> bool:
        self.iteration += 1
        if self.max_iterations > 1:
            if self.iteration == 1:
                self.add_message(
                    {
                        "role": "user",
                        "content": PROMPT_FIRST_ITERATION.format(
                            remaining_iterations=self.max_iterations - self.iteration
                        ),
                    }
                )
            elif self.iteration < self.max_iterations:
                self.add_message(
                    {
                        "role": "user",
                        "content": PROMPT_MIDDLE_ITERATION.format(
                            remaining_iterations=self.max_iterations - self.iteration
                        ),
                    }
                )
            else:
                self.add_message({"role": "user", "content": PROMPT_FINAL_ITERATION})
        return self.iteration <= self.max_iterations

    @abstractmethod
    def _generate_response(self, completion_kwargs: dict) -> any:
        raise NotImplementedError()

    @abstractmethod
    def _execute_iteration(self) -> str | None:
        raise NotImplementedError()

    def invoke(self, prompt: str | None = None) -> str | BaseModel:
        self.iteration = 0
        if prompt is not None:
            self.add_message({"role": "user", "content": prompt})
        while self._increment_iterator_message():
            response = self._execute_iteration()
            if response is not None:
                if self.response_format is not None:
                    final_response = self.response_format(**json.loads(response))
                else:
                    final_response = response
                if self.log:
                    # TODO: find the last logged message, this is a hack to make the system faster by not logging on add_message
                    with get_session() as session:
                        for message in self.messages:
                            log_message = RuntimeLogAgentMessage(
                                agent_instance_id=self.agent_id, message=message
                            )
                            session.add(log_message)
                        session.commit()
                return final_response
        raise RuntimeError(
            "Agent failed to produce a valid response within the allowed iterations."
        )
