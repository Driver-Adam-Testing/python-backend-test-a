from enum import IntEnum
from typing import Self


class Lang(IntEnum):
    DEFAULT = 0
    C = 1
    CPP = 2

    @classmethod
    def from_ext(cls, ext: str) -> Self:
        match ext:
            case ".c" | ".h":
                return cls.C
            case ".cpp" | ".cc" | ".cxx" | ".c++" | ".hpp" | ".hh" | ".hxx" | ".h++":
                return cls.CPP
            case _:
                return cls.DEFAULT
