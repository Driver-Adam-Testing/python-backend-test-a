from pathlib import Path

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.treesitter_drivers.python_driver import PyDriverTree

from ..base import SymbolParser
from ..utils import build_containment_map, to_root_relative


class PythonParser(SymbolParser):
    language = "python"
    fqn_delimiter = "."
    tree = PyDriverTree

    def parse_file(
        self, fpath: Path, project_root: Path
    ) -> tuple[
        list[RawTreeSitterSymbolData],  # symbols
        list[RawTreeSitterSymbolData],  # imports
        dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],  # containment_map
    ]:
        code_str = fpath.read_text(encoding="utf8")
        root_rel_path = to_root_relative(fpath, project_root)

        driver = self.tree.from_code(code_str=code_str, file_path=root_rel_path)

        all_syms = driver.extract_all_symbols()
        containment_map = build_containment_map(symbols=all_syms)

        imports: list[str] = []

        for sym in all_syms:
            if sym.symbol_kind == SymbolKind.IMPORT and sym.name is not None:
                imports.append(sym)

        return all_syms, imports, containment_map
