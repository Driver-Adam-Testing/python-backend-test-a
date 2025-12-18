from shared.inspector.utils.symbol_table.base import SymbolParser
from shared.inspector.utils.treesitter_drivers.ruby_driver import RubyDriverTree


class RubyParser(SymbolParser):
    language = "ruby"
    fqn_delimiter = "::"
    tree = RubyDriverTree
