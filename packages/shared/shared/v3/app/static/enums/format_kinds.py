from enum import Enum


class FormatKind(str, Enum):
    CODE_EXAMPLE = "CODE_EXAMPLE"
    DIAGRAM = "DIAGRAM"
    TEXT = "TEXT"
    TABLE = "TABLE"
    LIST = "LIST"
    ANY = "ANY"
