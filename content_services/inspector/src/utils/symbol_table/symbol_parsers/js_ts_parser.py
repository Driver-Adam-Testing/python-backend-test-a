from utils.symbol_table.base import SymbolParser
from utils.treesitter_drivers.js_ts_driver import (
    JsTsDriverTree,
)


class JsTsParser(SymbolParser):
    language = "js_ts"
    fqn_delimiter = "."
    tree = JsTsDriverTree
