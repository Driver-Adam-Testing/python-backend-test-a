from utils.symbol_table.base import SymbolParser
from utils.treesitter_drivers.java_driver import JavaDriverTree


class JavaParser(SymbolParser):
    language = "java"
    fqn_delimiter = "."
    tree = JavaDriverTree
