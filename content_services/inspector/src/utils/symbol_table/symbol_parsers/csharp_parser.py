from utils.treesitter_drivers.csharp_driver import CSharpDriverTree

from ..base import SymbolParser


class CSharpParser(SymbolParser):
    language = "csharp"
    fqn_delimiter = "."
    tree = CSharpDriverTree
