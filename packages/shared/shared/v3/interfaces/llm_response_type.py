from abc import ABC, abstractmethod

from shared.v3.utils.parseable import LlmParseable


class LlmResponseType(LlmParseable, ABC):
    @abstractmethod
    def to_markdown(self) -> str:
        raise NotImplementedError
