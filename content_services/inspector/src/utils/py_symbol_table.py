import sys
from os import sep
from pathlib import Path

# Add the src directory to Python path so imports work
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.py_driver_tree import PyDriverTree
from utils.symbol_table import (
    LinkedProject,
    ParsedProject,
    ParsedProjectWithVisibility,
    ReifiedProjectIndex,
    build_containment_map,
    to_root_relative,
)


def parse_py_file(
    fpath: Path,
    project_root: Path,
) -> tuple[
    list[RawTreeSitterSymbolData],
    list[str],
    dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],
]:
    code_str = fpath.read_text(encoding="utf8")
    root_rel_path = to_root_relative(fpath, project_root)

    driver = PyDriverTree.from_code(code_str=code_str, file_path=root_rel_path)

    all_syms = driver.extract_all_symbols()
    containment_map = build_containment_map(symbols=all_syms)

    imports: list[str] = []
    non_import_symbols: list[RawTreeSitterSymbolData] = []

    for sym in all_syms:
        if sym.symbol_kind == SymbolKind.IMPORT and sym.name is not None:
            imports.append(sym.name)
        else:
            non_import_symbols.append(sym)

    return non_import_symbols, imports, containment_map


def discover_py_files(project_root: Path) -> list[Path]:
    return [p.resolve() for p in project_root.rglob("*.py") if p.is_file()]


def resolve_import_path(
    current_file: Path, import_str: str, project_files: set[Path]
) -> Path | None:
    project_files_lst = list(project_files)

    import_str_pathified = Path(import_str.replace(".", sep)).with_suffix(".py")

    # 1) For cases like `import my_module` implemented in `/some_path/my_module.py`
    candidate = import_str_pathified
    for idx, f in enumerate(project_files_lst):
        if str(candidate) in str(f):
            return project_files_lst[idx]
        elif str(candidate.parent) == ".":
            # Avoid adding `import random` erroniously in the next section when using `parent`
            return None

    # 2) For `from my_module import fn` or `import my_module.fn` in `/some_path/my_module.py`
    try:
        candidate = import_str_pathified.parent.with_suffix(".py")
    except ValueError:
        # import_str_pathified.parent is just "/" or similar in this case, and can't be resolved
        return None
    for idx, f in enumerate(project_files_lst):
        if str(candidate) in str(f):
            return project_files_lst[idx]

    # 3) TODO: Figure out how to handle subfolders as modules (with __init__.py)

    return None


def build_py_project_index(
    file_paths: list[Path], project_root: Path
) -> ReifiedProjectIndex:
    """
    Orchestrate the 4 passes:
      1) Parse each file
      2) Determine transitive visibility among those files
      3) Link usage -> definition
      4) definition -> usage
    """
    print("==> Parsing files...")
    parsed = ParsedProject.from_files(
        file_paths=file_paths,
        project_root=project_root,
        parse_file_fn=parse_py_file,
        num_workers=8,
    )
    print("==> Resolving includes and visibility...")
    project_vis = ParsedProjectWithVisibility.from_parsed_project(
        parsed=parsed, resolver_fn=resolve_import_path, num_workers=8
    )
    print("==> Linking symbols...")
    linked = LinkedProject.from_parsed_project_with_visibility(
        project_vis=project_vis, sep="."
    )
    print("==> Reifying symbol graph...")
    reified = ReifiedProjectIndex.from_linked_project(
        linked_proj=linked, file_to_containment_map=parsed.file_to_containment_map
    )
    print("==> Done building index.")
    return reified


def main() -> ReifiedProjectIndex:
    project_root = Path(
        "/Users/daniel/Documents/moved_content_from_python_backend/infinity-core"
    )
    file_paths = discover_py_files(project_root=project_root)
    print(file_paths)
    index = build_py_project_index(file_paths=file_paths, project_root=project_root)
    index.print_summary(sep=".")

    return index


if __name__ == "__main__":
    main()
