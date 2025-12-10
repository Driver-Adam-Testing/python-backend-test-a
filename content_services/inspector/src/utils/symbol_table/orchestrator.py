from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import Lang, ReifiedSymbol, SymbolKind

from .base import LanguageProvider
from .comparison import TimingInfo, timer
from .core import (
    LinkedProject,
    ParsedProject,
    ParsedProjectWithVisibility,
    ReifiedProjectIndex,
)
from .language_utils import get_language_providers
from .utils import get_fully_qualified_name


def build_symbol_table(
    file_paths: list[Path],
    project_root: Path,
    num_workers: int | None = 8,
    return_timing: bool = False,
) -> (
    dict[Path, list[ReifiedSymbol]] | tuple[dict[Path, list[ReifiedSymbol]], TimingInfo]
):
    """
    Generic symbol table builder that:
    1. Groups files by detected language
    2. Builds language-specific symbol tables
    3. Returns unified mapping of path -> symbols
    """

    providers = get_language_providers()

    language_groups: dict[str, list[Path]] = defaultdict(list)
    unsupported_files: list[Path] = []

    for file_path in file_paths:
        lang = Lang.from_ext(file_path.suffix)
        match lang:
            case Lang.C | Lang.CPP | Lang.C_OR_CPP_HEADER:
                language_groups["c_cpp"].append(file_path)
            case Lang.PYTHON:
                language_groups["python"].append(file_path)
            case Lang.JAVA:
                language_groups["java"].append(file_path)
            case Lang.C_SHARP:
                language_groups["csharp"].append(file_path)
            case Lang.TYPESCRIPT | Lang.JAVASCRIPT:
                language_groups["js_ts"].append(file_path)
            case Lang.GO:
                language_groups["go"].append(file_path)
            case Lang.RUBY:
                language_groups["ruby"].append(file_path)
            case _:
                unsupported_files.append(file_path)

    if unsupported_files:
        print(
            f"{len(unsupported_files)} unsupported files due to no symbol table provider for them"
        )

    unified_result: dict[Path, list[ReifiedSymbol]] = {}
    total_timing = TimingInfo()

    for lang, lang_files in language_groups.items():
        if not lang_files:
            continue

        provider = providers[lang]
        print(f"==> Building {lang} symbol table for {len(lang_files)} files")

        if return_timing:
            index, timing = _build_language_symbol_table(
                file_paths=lang_files,
                project_root=project_root,
                provider=provider,
                num_workers=num_workers,
                return_timing=True,
            )
            total_timing = total_timing + timing
        else:
            index = _build_language_symbol_table(
                file_paths=lang_files,
                project_root=project_root,
                provider=provider,
                num_workers=num_workers,
                return_timing=False,
            )

        unified_result.update(index.file_to_symbols)

    if return_timing:
        return unified_result, total_timing
    return unified_result


def _build_language_symbol_table(
    file_paths: list[Path],
    project_root: Path,
    provider: LanguageProvider,
    num_workers: int | None = 8,
    return_timing: bool = False,
) -> ReifiedProjectIndex | tuple[ReifiedProjectIndex, TimingInfo]:
    parser = provider.get_parser()
    resolver = provider.get_resolver()

    timing = TimingInfo()

    print("==> Parsing files...")
    with timer() as parse_timer:
        parsed = ParsedProject.from_files(
            file_paths,
            project_root,
            parser=parser,
            num_workers=num_workers,
        )
    timing.parsing_time = parse_timer["elapsed"]

    print("==> Resolving includes and visibility...")
    # Always get timing for visibility since it's the key operation
    project_vis, vis_timing = ParsedProjectWithVisibility.from_parsed_project(
        parsed,
        resolver=resolver,
        num_workers=num_workers,
        return_timing=True,
    )
    timing.visibility_time = vis_timing.visibility_time
    print(f"    Visibility computation took {vis_timing.visibility_time:.3f}s")

    print("==> Linking symbols...")
    with timer() as link_timer:
        linked = LinkedProject.from_parsed_project_with_visibility(
            project_vis, sep=provider.get_fqn_delimiter()
        )
    timing.linking_time = link_timer["elapsed"]

    print("==> Reifying symbol graph...")
    with timer() as reify_timer:
        result = ReifiedProjectIndex.from_linked_project(
            linked, parsed.file_to_containment_map
        )
    timing.reification_time = reify_timer["elapsed"]
    timing.total_time = (
        timing.parsing_time
        + timing.visibility_time
        + timing.linking_time
        + timing.reification_time
    )

    if return_timing:
        return result, timing
    return result


def print_summary(
    symbol_table: dict[Path, list[ReifiedSymbol]],
    files: list[Path] | None = None,
    sep: str = "::",
) -> None:
    """
    Print a colorized summary of symbols in the symbol table.

    Args:
        symbol_table: Dictionary mapping file paths to lists of ReifiedSymbol
        files: Optional list of files to filter on. If None, shows all files.
        sep: Separator for fully qualified names (default "::")
    """
    RESET = "\033[0m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    ORANGE = "\033[38;5;208m"

    targets = files if files else sorted(symbol_table.keys())

    for fpath in targets:
        reified_syms = symbol_table.get(fpath)
        if reified_syms is None:
            print(f"{YELLOW}No symbols found for {fpath}{RESET}")
            continue

        print(f"\n{BOLD}{BLUE}File: {fpath}{RESET}")
        for sym in reified_syms:
            name = sym.raw.name
            lines = f"[lines {sym.raw.start_line}-{sym.raw.end_line}]"

            # Show fully qualified name for symbols with qualified parent paths
            fqn = get_fully_qualified_name(sym=sym.raw, sep=sep)
            name_display = fqn if sym.raw.fully_qualified_parent_path else name

            if sym.is_definition:
                usage_count = len(sym.usages)
                decl_count = len(sym.declarations)

                # Special handling for classes/structs
                if (
                    sym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE
                    or sym.raw.symbol_kind == SymbolKind.CLASS
                ):
                    members = sym.children
                    member_functions = [
                        m for m in members if m.raw.symbol_kind == SymbolKind.CALLABLE
                    ]
                    member_variables = [
                        m for m in members if m.raw.symbol_kind == SymbolKind.VARIABLE
                    ]
                    member_func_count = len(member_functions)
                    member_var_count = len(member_variables)
                    print(
                        f"{GREEN}  📦 CLASS/STRUCT: {BOLD}{name_display}{RESET}{GREEN} {lines} "
                        f"[{usage_count} usage(s), {decl_count} declaration(s)]{RESET}"
                    )

                    if member_func_count > 0 or member_var_count > 0:
                        print(
                            f"     {BOLD}Members:{RESET} {member_func_count} function(s), {member_var_count} variable(s)"
                        )

                    # Show member functions
                    if member_functions:
                        print(f"     {BOLD}Functions:{RESET}")
                        for member_func in member_functions:
                            mf_name = member_func.raw.name
                            mf_lines = f"[lines {member_func.raw.start_line}-{member_func.raw.end_line}]"
                            mf_usage_count = len(member_func.usages)
                            print(
                                f"{RED}       🔧 {mf_name} {mf_lines} [{mf_usage_count} usage(s)]{RESET}"
                            )

                    # Show member variables
                    if member_variables:
                        print(f"     {BOLD}Variables:{RESET}")
                        for member_var in member_variables:
                            mv_name = member_var.raw.name
                            mv_lines = f"[lines {member_var.raw.start_line}-{member_var.raw.end_line}]"
                            mv_usage_count = len(member_var.usages)
                            print(
                                f"{RED}       📌 {mv_name} {mv_lines} [{mv_usage_count} usage(s)]{RESET}"
                            )
                    if sym.inherits_from:
                        print(
                            f"     {BOLD}Inheritance:{RESET} "
                            f"{', '.join(get_fully_qualified_name(i.raw, sep) for i in sym.inherits_from)}"
                        )
                else:
                    # Check if this is a member function
                    is_member = sym.raw.fully_qualified_parent_path is not None
                    icon = "🔧" if sym.raw.symbol_kind == SymbolKind.CALLABLE else "📍"
                    member_prefix = "MEMBER " if is_member else ""

                    print(
                        f"{GREEN}  {icon} {member_prefix}DEF: {BOLD}{name_display}{RESET}{GREEN} {lines} "
                        f"[{usage_count} usage(s), {decl_count} declaration(s)]{RESET}"
                    )

                    # Show the containing class if this is a member
                    if is_member:
                        containing = sym.parent
                        if containing:
                            print(
                                f"     {BOLD}Member of:{RESET} {get_fully_qualified_name(containing.raw, sep)} [lines {containing.raw.start_line}-{containing.raw.end_line}] "
                            )

                # Show declarations for this definition
                if sym.declarations:
                    print(f"     {BOLD}Declarations:{RESET}")
                    for decl_sym in sym.declarations:
                        decl_name = get_fully_qualified_name(sym=decl_sym.raw, sep=sep)
                        decl_lines = (
                            f"[lines {decl_sym.raw.start_line}-"
                            f"{decl_sym.raw.end_line}]"
                        )
                        decl_file_path = decl_sym.raw.file_path
                        print(
                            f"{MAGENTA}       📄 {decl_name} {decl_lines} "
                            f"in {decl_file_path}{RESET}"
                        )

                # If this is a CALLABLE definition, show the calls it makes
                if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.calls:
                    print(f"     {BOLD}Calls {len(sym.calls)} function(s):{RESET}")
                    for called_func in sym.calls:
                        called_name = get_fully_qualified_name(
                            sym=called_func.raw, sep=sep
                        )
                        c_lines = (
                            f"[lines {called_func.raw.start_line}-"
                            f"{called_func.raw.end_line}]"
                        )
                        c_path = called_func.raw.file_path
                        print(
                            f"       ↪️  {ORANGE}{called_name} {c_lines} in {c_path}{RESET}"
                        )

                # Show usages
                if sym.usages:
                    print(f"     {BOLD}Used in:{RESET}")
                    for _i, usage_sym in enumerate(sym.usages[:5]):  # Limit to first 5
                        usage_lines = (
                            f"[lines {usage_sym.raw.start_line}-"
                            f"{usage_sym.raw.end_line}]"
                        )
                        usage_file_path = usage_sym.raw.file_path
                        print(
                            f"{YELLOW}       🔗 {usage_lines} "
                            f"in {usage_file_path}{RESET}"
                        )
                    if len(sym.usages) > 5:
                        print(f"       ... and {len(sym.usages) - 5} more usage(s)")

            elif sym.is_declaration:
                if sym.definition:
                    def_name = get_fully_qualified_name(sym=sym.definition.raw, sep=sep)
                    def_lines = (
                        f"[lines {sym.definition.raw.start_line}-"
                        f"{sym.definition.raw.end_line}]"
                    )
                    def_file_path = sym.definition.raw.file_path
                    print(
                        f"{CYAN}  📋 DECL: {BOLD}{name_display}{RESET}{CYAN} {lines} "
                        f"-> DEF: {def_name} {def_lines} in {def_file_path}{RESET}"
                    )
                else:
                    print(
                        f"{CYAN}  📋 DECL: {BOLD}{name_display}{RESET}{CYAN} {lines} "
                        f"[no definition found]{RESET}"
                    )
            else:
                pass
                # Usage
                # if sym.definition:
                #     def_name = get_fully_qualified_name(sym=sym.definition.raw, sep=sep)
                #     def_lines = (
                #         f"[lines {sym.definition.raw.start_line}-"
                #         f"{sym.definition.raw.end_line}]"
                #     )
                #     def_file_path = sym.definition.raw.file_path
                #     print(
                #         f"{YELLOW}  🔗 USE: {BOLD}{name_display}{RESET}{YELLOW} {lines} "
                #         f"-> DEF: {def_name} {def_lines} in {def_file_path}{RESET}"
                #     )
                # else:
                #     print(
                #         f"{YELLOW}  🔗 USE: {BOLD}{name_display}{RESET}{YELLOW} {lines} "
                #         f"[no definition found]{RESET}"
                #     )
