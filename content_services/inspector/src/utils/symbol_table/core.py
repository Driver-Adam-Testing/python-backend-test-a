from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Self

from utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    ReifiedSymbol,
    SymbolKind,
)

from .base import SymbolParser, SymbolResolver
from .comparison import TimingInfo, timer
from .utils import (
    disambiguate_call,
    get_fully_qualified_name,
    is_data_structure,
    is_declaration,
    is_definition,
)

MAX_DISAMBIGUATIONS_PER_LANGUAGE = 10_000  # NOTE: This is all or nothing - if we exceed this, we disable disambiguation for the language


def parse_and_handle(
    abs_fpath: Path, parser: SymbolParser, project_root: str
) -> tuple[Path, list, list, dict]:
    from .utils import to_root_relative

    rel_fpath = to_root_relative(abs_fpath, project_root)
    try:
        symbols, includes, containment_map = parser.parse_file(abs_fpath, project_root)
    except Exception as e:
        print(f"  Warning: Failed to parse {rel_fpath}: {e}")
        symbols, includes, containment_map = [], [], {}
    return rel_fpath, symbols, includes, containment_map


@dataclass(frozen=True)
class ParsedProject:
    file_to_symbols: dict[
        Path, list[RawTreeSitterSymbolData]
    ]  # Path here is `myproject/my_path/file.c`
    includes_map: dict[
        Path, list[RawTreeSitterSymbolData]
    ]  # Path here is `myproject/my_path/file.c`
    file_to_containment_map: dict[
        Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
    ]  # Path here is `myproject/my_path/file.c`

    @classmethod
    def from_files(
        cls,
        file_paths: list[Path],
        project_root: Path,
        parser: SymbolParser,
        num_workers: int | None = None,
    ) -> Self:
        file_to_syms = {}
        raw_includes = {}
        file_to_containment_map = {}

        if num_workers is None or num_workers == 1:
            # Serial processing
            total = len(file_paths)
            for i, abs_fpath in enumerate(file_paths, 1):
                if i % 25 == 0 or i == total:
                    print(f"  Parsing files... [{i}/{total}]", flush=True)
                rel_fpath, symbols, includes, containment_map = parse_and_handle(
                    abs_fpath
                )
                file_to_syms[rel_fpath] = symbols
                raw_includes[rel_fpath] = includes
                file_to_containment_map[rel_fpath] = containment_map
        else:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                future_to_path = {
                    executor.submit(parse_and_handle, fp, parser, project_root): fp
                    for fp in file_paths
                }
                total = len(file_paths)
                for i, future in enumerate(as_completed(future_to_path), 1):
                    rel_fpath, symbols, includes, containment_map = future.result()
                    if i % 25 == 0 or i == total:
                        print(f"  Parsing files... [{i}/{total}]", flush=True)
                    file_to_syms[rel_fpath] = symbols
                    raw_includes[rel_fpath] = includes
                    file_to_containment_map[rel_fpath] = containment_map

        return cls(
            file_to_symbols=file_to_syms,
            includes_map=raw_includes,
            file_to_containment_map=file_to_containment_map,
        )


@dataclass(frozen=True)
class ParsedProjectWithVisibility:
    """
    - Same data as ParsedProject
    - Add a visibility_map that tells you which symbols are visible from each file.
    """

    file_to_symbols: dict[Path, list[RawTreeSitterSymbolData]]
    includes_map: dict[Path, list[RawTreeSitterSymbolData]]
    visibility_map: dict[Path, set[RawTreeSitterSymbolData]]

    @classmethod
    def from_parsed_project(
        cls,
        parsed: ParsedProject,
        num_workers: int | None,
        resolver: SymbolResolver,
        return_timing: bool = False,
    ) -> Self | tuple[Self, TimingInfo]:
        """
        Build a map from each file -> all files it can 'see' transitively.
        Only links includes that are in parsed.file_to_symbols (our project).

        return_timing: Whether to return timing information
        """
        file_to_symbols = parsed.file_to_symbols
        includes_map = parsed.includes_map

        timing = TimingInfo()

        with timer() as visibility_timer:
            visibility_map = resolver.resolve_imports_to_symbols(
                all_files_imports=includes_map,
                all_files_symbols=file_to_symbols,
                num_workers=num_workers,
            )
        timing.visibility_time = visibility_timer["elapsed"]

        result = cls(
            file_to_symbols=file_to_symbols,
            includes_map=includes_map,
            visibility_map=visibility_map,
        )

        if return_timing:
            return result, timing
        return result


@dataclass(frozen=True)
class LinkedSymbol:
    """
    Extends RawTreeSitterSymbolData with a pointer to a definition
    if this is a usage (definition=None if it is itself a definition).
    """

    raw: RawTreeSitterSymbolData
    is_definition: bool
    is_declaration: bool
    is_base_class: bool = False
    base_name: str | None = None
    definition: Self | None = None


@dataclass(frozen=True)
class LinkedProject:
    """
    Results in
    - A dictionary from file -> list of LinkedSymbol
    - Carries forward the same visibility_map
    """

    linked_symbols: dict[Path, list[LinkedSymbol]]
    visibility_map: dict[Path, set[RawTreeSitterSymbolData]]

    @classmethod
    def from_parsed_project_with_visibility(
        cls,
        project_vis: ParsedProjectWithVisibility,
        sep: str = "::",
    ) -> Self:
        """
        Link usage -> definition across all files that are transitively visible.
        """
        # 1) Collect definitions and declarations by name
        definitions_by_fqn: dict[str, list[tuple[str, RawTreeSitterSymbolData]]] = {}
        definitions_by_name: dict[str, list[tuple[Path, RawTreeSitterSymbolData]]] = {}
        declarations_by_fqn: dict[str, list[tuple[str, RawTreeSitterSymbolData]]] = {}

        file_to_symbols = dict()
        for k, v in project_vis.file_to_symbols.items():
            new_v = []
            for sym in v:
                if sym.symbol_kind != SymbolKind.IMPORT:
                    new_v.append(sym)
            file_to_symbols[k] = new_v

        for fpath, raw_syms in file_to_symbols.items():
            for rsym in raw_syms:
                if rsym.name is None:
                    continue
                fqn = get_fully_qualified_name(sym=rsym, sep=sep)
                if is_definition(rsym):
                    definitions_by_fqn.setdefault(fqn, []).append((fqn, rsym))
                    definitions_by_name.setdefault(rsym.name, []).append((fpath, rsym))
                elif is_declaration(rsym):
                    declarations_by_fqn.setdefault(fqn, []).append((fqn, rsym))
                # else it's a usage or something else

        # 2) If there's exactly 1 definition for a name, unify all declarations to it
        decl_to_def: dict[RawTreeSitterSymbolData, RawTreeSitterSymbolData] = {}
        for fqn, decl_list in declarations_by_fqn.items():
            def_list = definitions_by_fqn.get(fqn, [])
            if len(def_list) == 1:
                (def_fpath, def_sym) = def_list[0]
                for _decl_fpath, decl_sym in decl_list:
                    decl_to_def[decl_sym] = def_sym

        # 3) For each symbol, link usage->definition if visible
        linked_map: dict[Path, list[LinkedSymbol]] = {}

        def _process_file(
            visible_with_self: set[RawTreeSitterSymbolData],
            raw_syms: list[RawTreeSitterSymbolData],
            do_disambiguation: bool,
        ) -> list[LinkedSymbol]:
            llm_calls_made_this_file = 0

            linked_syms: list[LinkedSymbol] = []
            for rsym in raw_syms:
                def_symbol: LinkedSymbol | None = None
                fqn = get_fully_qualified_name(sym=rsym, sep=sep)

                if not is_definition(rsym) and not is_declaration(rsym) and rsym.name:
                    # Direct definitions in visible files
                    if rsym.symbol_kind == SymbolKind.CALL:
                        candidates = definitions_by_name.get(rsym.name, [])
                    else:
                        candidates = definitions_by_fqn.get(fqn, [])
                    candidate_defs = [
                        (dfpath, dfsym)
                        for (dfpath, dfsym) in candidates
                        if dfsym in visible_with_self
                    ]
                    # candidate_defs = []
                    # for vis_sym in visible_with_self:
                    #     if is_definition(vis_sym) and vis_sym.name == rsym.name:
                    #         candidate_defs.append((vis_sym.file_path, vis_sym))

                    vis_defs = []
                    for candidate_def in candidate_defs:
                        if (
                            candidate_def[1].file_path == rsym.file_path
                            and candidate_def[1].start_byte < rsym.start_byte
                            and candidate_def[1].end_byte >= rsym.end_byte
                        ):
                            # This would only occur in the case of a recursion.
                            # So we choose to not link it to itself.
                            continue
                        vis_defs.append(candidate_def)
                    if len(vis_defs) == 1:
                        dfpath, def_raw = vis_defs[0]
                        def_symbol = LinkedSymbol(
                            raw=def_raw,
                            is_definition=True,
                            is_declaration=False,
                            definition=None,
                        )
                    elif len(vis_defs) > 1 and do_disambiguation:
                        # If we can't disambiguate successfully, we do not link this symbol
                        def_raw = None
                        # This is true even for FQN though due overloading
                        if rsym.symbol_kind == SymbolKind.CALL:
                            # Disambiguate
                            calling_symbol = definitions_by_fqn.get(
                                rsym.fully_qualified_parent_path, []
                            )
                            # TODO: disambiguate calling symbol !
                            if len(calling_symbol) > 0:
                                index, llm_called = disambiguate_call(
                                    vis_defs,
                                    rsym,
                                    calling_symbol[0][1],
                                )
                                if llm_called:
                                    llm_calls_made_this_file += 1
                                if index is not None and index < len(vis_defs):
                                    dfpath, def_raw = vis_defs[index]
                                    # TODO: if we fail to get here, default to first element
                                else:
                                    dfpath = None
                                    def_raw = None
                        if def_raw is not None:
                            def_symbol = LinkedSymbol(
                                raw=def_raw,
                                is_definition=True,
                                is_declaration=False,
                                definition=None,
                            )
                    else:
                        # No direct definition, check for declarations
                        # TODO: this works for C, but C++ may have issues with namespaces that limit this
                        decl_candidates = declarations_by_fqn.get(rsym.name, [])
                        vis_decls = [
                            (dpath, d_raw)
                            for (dpath, d_raw) in decl_candidates
                            if d_raw in visible_with_self
                        ]
                        if len(vis_decls) >= 1:
                            # pick first for simplicity
                            _, decl_raw = vis_decls[0]
                            # see if we unified this decl to a known definition
                            maybe_def = decl_to_def.get(decl_raw)
                            if maybe_def is not None:
                                def_symbol = LinkedSymbol(
                                    raw=maybe_def,
                                    is_definition=True,
                                    is_declaration=False,
                                    definition=None,
                                )

                elif is_declaration(rsym) and rsym.name and rsym in decl_to_def:
                    def_symbol = LinkedSymbol(
                        raw=decl_to_def[rsym],
                        is_definition=True,
                        is_declaration=False,
                        definition=None,
                    )
                elif is_definition(rsym) and is_data_structure(rsym):
                    # For DATA_STRUCTURE, we look for base classes
                    if (
                        rsym.base_class_names is not None
                        and len(rsym.base_class_names) > 0
                    ):
                        for base_name in rsym.base_class_names:
                            candidates = definitions_by_name.get(base_name, [])
                            fqn_candidates = definitions_by_fqn.get(base_name, [])
                            for fqn_candidate in fqn_candidates:
                                if fqn_candidate not in candidates:
                                    candidates.append(fqn_candidate)
                            vis_defs = [
                                (_dfpath, dfsym)
                                for (_dfpath, dfsym) in candidates
                                if dfsym in visible_with_self
                                and is_data_structure(dfsym)
                            ]
                            if len(vis_defs) >= 1:
                                # pick first or unify
                                dfpath, def_raw = vis_defs[0]
                                # TODO: hack. Better way is to extract base classes in DriverTree classes
                                # and use other symbol table mechanics to link them
                                linked_syms.append(
                                    LinkedSymbol(
                                        raw=def_raw,
                                        is_definition=False,
                                        is_declaration=False,
                                        is_base_class=True,
                                        base_name=base_name,
                                        definition=None,
                                    )
                                )

                linked_syms.append(
                    LinkedSymbol(
                        raw=rsym,
                        is_definition=is_definition(rsym),
                        is_declaration=is_declaration(rsym),
                        definition=def_symbol,
                    )
                )
            return linked_syms

        # NOTE: Heuristic on total number of calls
        total_calls = sum(
            1
            for _, raw_syms in file_to_symbols.items()
            for rsym in raw_syms
            if rsym.symbol_kind == SymbolKind.CALL
        )
        do_disambiguation = total_calls <= MAX_DISAMBIGUATIONS_PER_LANGUAGE

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_path = {}
            for fpath, raw_syms in file_to_symbols.items():
                # visible_files = project_vis.visibility_map.get(fpath, set())
                # visible_with_self = {fpath, *visible_file

                visible_syms = project_vis.visibility_map.get(fpath, set())
                visible_with_self = {*file_to_symbols[fpath], *visible_syms}
                future_to_path[
                    executor.submit(
                        _process_file, visible_with_self, raw_syms, do_disambiguation
                    )
                ] = fpath
            for future in as_completed(future_to_path):
                fpath = future_to_path[future]
                linked_syms = future.result()
                linked_map[fpath] = linked_syms

        return cls(linked_symbols=linked_map, visibility_map=project_vis.visibility_map)


@dataclass(frozen=True)
class ReifiedProjectIndex:
    """
    Final result:
      - A dictionary from file -> reified symbols (fully linked in both directions).
      - A mapping from object FQNs to their member functions and variables for C++
    """

    file_to_symbols: dict[Path, list[ReifiedSymbol]]

    @classmethod
    def from_linked_project(
        cls,
        linked_proj: LinkedProject,
        file_to_containment_map: dict[
            Path, dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]]
        ],
    ) -> Self:
        # (1) Create provisional ReifiedSymbols
        provisional_map: dict[LinkedSymbol, ReifiedSymbol] = {}

        # Track classes/structs/etc and their members
        obj_symbols: dict[str, ReifiedSymbol] = {}  # fqn -> ReifiedSymbol
        obj_members: dict[str, dict[str, list[ReifiedSymbol]]] = defaultdict(
            lambda: {"functions": [], "variables": []}
        )

        for _fpath, ls_list in linked_proj.linked_symbols.items():
            for lsym in ls_list:
                provisional_map[lsym] = ReifiedSymbol(
                    raw=lsym.raw,
                    is_definition=lsym.is_definition,
                    is_declaration=lsym.is_declaration,
                )

        # (2) Build adjacency from definition => usage
        def_to_usage: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        def_to_decl: dict[LinkedSymbol, list[LinkedSymbol]] = {}
        for lsym in provisional_map:
            if not lsym.is_definition and lsym.definition is not None:
                def_ls = lsym.definition

                if is_declaration(lsym.raw):
                    def_to_decl.setdefault(def_ls, []).append(lsym)
                else:  # Usage
                    def_to_usage.setdefault(def_ls, []).append(lsym)

        # (3) Build a first pass final_map that sets .definition and .usages
        final_map: dict[LinkedSymbol, ReifiedSymbol] = {}
        for lsym, reified_sym in provisional_map.items():
            new_def = None
            if (not lsym.is_definition) and lsym.definition:
                new_def = provisional_map[lsym.definition]
            usage_list = [provisional_map[u] for u in def_to_usage.get(lsym, [])]
            decl_list = [provisional_map[d] for d in def_to_decl.get(lsym, [])]
            final_map[lsym] = replace(
                reified_sym,
                definition=new_def,
                usages=usage_list,
                declarations=decl_list,
            )

            # Track class/object definitions
            if lsym.is_definition and is_data_structure(lsym.raw):
                fqn = get_fully_qualified_name(sym=lsym.raw)
                # TODO: This isn't actually unique due to partial classes in C#, their FQN will be the same
                obj_symbols[fqn] = final_map[lsym]

        # (4) For function definitions, gather calls from the containment map
        raw_to_linked: dict[RawTreeSitterSymbolData, LinkedSymbol] = {}
        for lsym in final_map:
            raw_to_linked[lsym.raw] = lsym

        for fpath, ls_list in linked_proj.linked_symbols.items():
            containment_map = file_to_containment_map.get(fpath, {})
            for lsym in ls_list:
                if lsym.is_definition and lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                    children = containment_map.get(lsym.raw, [])
                    calls_made: list[ReifiedSymbol] = []
                    for child_raw in children:
                        if child_raw.symbol_kind == SymbolKind.CALL:
                            child_linked_sym = raw_to_linked[child_raw]
                            if child_linked_sym.definition is not None:
                                called_func_reif = final_map[
                                    child_linked_sym.definition
                                ]
                                calls_made.append(called_func_reif)

                    old_reif = final_map[lsym]
                    final_map[lsym] = replace(old_reif, calls=calls_made)
                elif is_data_structure(lsym.raw):
                    # Set inheritance
                    if lsym.raw.base_class_names is not None:
                        inherits_from: list[ReifiedSymbol] = []
                        for base_class in lsym.raw.base_class_names:
                            # Find a matching linked symbol
                            for base_ls in ls_list:
                                if (
                                    base_ls.is_base_class
                                    and base_ls.base_name == base_class
                                ):
                                    # We found a base class in the same file
                                    inherits_from.append(final_map[base_ls])
                                    break
                        if len(inherits_from):
                            old_reif = final_map[lsym]
                            final_map[lsym] = replace(
                                old_reif,
                                inherits_from=inherits_from,
                            )
                    # Handle partial classes/structs/interfaces in C#
                    # if fpath.suffix == ".cs":
                    #     bespoke_data = lsym.raw.bespoke_data
                    #     if "partial" in bespoke_data.modifiers:
                    #         # Find other partial definitions in other files
                    #         fqn = get_fully_qualified_name(sym=lsym.raw)

                    #         for (
                    #             fpath_partial,
                    #             lsym_partial_list,
                    #         ) in linked_proj.linked_symbols.items():
                    #             if fpath_partial == fpath:
                    #                 continue
                    #             for lsym_partial in lsym_partial_list:
                    #                 if is_data_structure(lsym_partial.raw):
                    #                     fqn2 = get_fully_qualified_name(
                    #                         sym=lsym_partial.raw
                    #                     )
                    #                     if fqn == fqn2:
                    #                         final_map[lsym].children.append(
                    #                             final_map[lsym_partial]
                    #                         )

        # (5) Build object membership dicts
        for lsym, reified in final_map.items():
            if lsym.is_definition and lsym.raw.fully_qualified_parent_path:
                parent_fqn = lsym.raw.fully_qualified_parent_path

                # Check if this symbol belongs to a known class
                if True:  # lsym.raw.file_path.suffix != ".cs":
                    if parent_fqn in obj_symbols:
                        if lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                            obj_members[parent_fqn]["functions"].append(reified)
                            parent_sym = obj_symbols[parent_fqn]
                            reified.parent = parent_sym
                            parent_sym.children.append(reified)
                        # Since we only pull globals, empty right now... TODO
                        elif lsym.raw.symbol_kind == SymbolKind.VARIABLE:
                            obj_members[parent_fqn]["variables"].append(reified)
                            parent_sym = obj_symbols[parent_fqn]
                            reified.parent = parent_sym
                            parent_sym.children.append(reified)
                else:
                    # In C# we need to deal with partial classes,
                    # the obj_symbols and obj_members only have one part of the partial class
                    if lsym.raw.symbol_kind == SymbolKind.CALLABLE:
                        for lsym_partial, reified_partial in final_map.items():
                            if lsym.raw.file_path != lsym_partial.raw.file_path:
                                continue
                            if parent_fqn == get_fully_qualified_name(lsym_partial.raw):
                                reified.parent = reified_partial
                                reified_partial.children.append(reified)

        # (6) Group them by file
        file_map: dict[Path, list[ReifiedSymbol]] = {}
        for fpath, ls_list in linked_proj.linked_symbols.items():
            file_map[fpath] = [final_map[ls] for ls in ls_list]

        return cls(file_to_symbols=file_map)
