import abc
from typing import Self

from utils.dag import FlatTopoFileDiffDag


class DiffUpdatable(abc.ABC):
    @abc.abstractmethod
    def update_from_diff(self, diff_collection: FlatTopoFileDiffDag) -> Self:
        pass
