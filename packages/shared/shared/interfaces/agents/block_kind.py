import enum


class BlockKind(str, enum.Enum):
    LIST = "LIST"
    TABLE = "TABLE"
    DIAGRAM = "DIAGRAM"
    CODE = "CODE"
    TEXT = "TEXT"
    ANY = "ANY"
