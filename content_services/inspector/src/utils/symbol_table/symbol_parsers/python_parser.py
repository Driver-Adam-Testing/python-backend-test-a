from utils.symbol_table.base import SymbolParser
from utils.treesitter_drivers.python_driver import PyDriverTree


class PythonParser(SymbolParser):
    language = "python"
    fqn_delimiter = "."
    tree = PyDriverTree
