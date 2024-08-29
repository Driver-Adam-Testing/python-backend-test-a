from abc import ABC, abstractmethod

from pydantic import BaseModel


class ToolStrict(BaseModel, ABC):
    @abstractmethod
    def execute(self, agent, **kwargs):
        pass
