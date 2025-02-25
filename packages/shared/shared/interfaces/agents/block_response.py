from abc import ABC, abstractmethod

from pydantic import BaseModel


class BlockResponse(BaseModel, ABC):
    @abstractmethod
    def to_markdown(self) -> str:
        pass
