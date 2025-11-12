from shared.inspector.utils.symbol_table.base import SymbolParser
from shared.inspector.utils.treesitter_drivers.c_cpp_driver import CppCDriverTree


class CCppParser(SymbolParser):
    language = "c_cpp"  # Shared parser for both C and C++
    fqn_delimiter = "::"
    tree = CppCDriverTree  # Use the C/C++ driver tree
