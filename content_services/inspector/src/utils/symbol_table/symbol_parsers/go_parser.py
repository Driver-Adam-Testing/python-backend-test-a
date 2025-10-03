from utils.treesitter_drivers.go_driver import GoDriverTree

from ..base import SymbolParser


class GoParser(SymbolParser):
    language = "go"
    fqn_delimiter = "/"
    tree = GoDriverTree
