from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.treesitter_drivers.c_cpp_driver import CppCDriverTree

from ..base import SymbolParser
from ..utils import build_containment_map, to_root_relative


class CCppParser(SymbolParser):
    language = "c_cpp"  # Shared parser for both C and C++
    fqn_delimiter = "::"

    def parse_file(
        self, fpath: Path, project_root: Path
    ) -> tuple[
        list[RawTreeSitterSymbolData],  # symbols
        list[str],  # imports
        dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],  # containment_map
    ]:
        code_str = fpath.read_text(encoding="utf8")
        root_rel_path = to_root_relative(fpath, project_root)

        driver = CppCDriverTree.from_code(code_str, file_path=root_rel_path)

        all_syms = driver.extract_all_symbols()
        containment_map = build_containment_map(all_syms)

        includes: list[str] = []
        non_import_symbols: list[RawTreeSitterSymbolData] = []

        for sym in all_syms:
            if sym.symbol_kind == SymbolKind.IMPORT and sym.name is not None:
                includes.append(sym.name)
            else:
                non_import_symbols.append(sym)

        return non_import_symbols, includes, containment_map
