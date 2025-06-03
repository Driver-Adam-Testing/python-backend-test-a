from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import ReifiedSymbol

from .core import (
    LinkedProject,
    ParsedProject,
    ParsedProjectWithVisibility,
    ReifiedProjectIndex,
)
from .language_utils import detect_language, get_language_providers


def build_symbol_table(
    file_paths: list[Path], project_root: Path, num_workers: int | None = 8
) -> dict[Path, list[ReifiedSymbol]]:
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
        lang = detect_language(file_path)
        if lang:
            language_groups[lang].append(file_path)
        else:
            unsupported_files.append(file_path)

    if unsupported_files:
        print(
            f"{len(unsupported_files)} unsupported files due to no symbol table provider for them"
        )

    unified_result: dict[Path, list[ReifiedSymbol]] = {}

    for lang, lang_files in language_groups.items():
        if not lang_files:
            continue

        provider = providers[lang]
        print(f"==> Building {lang} symbol table for {len(lang_files)} files")

        index = _build_language_symbol_table(
            file_paths=lang_files,
            project_root=project_root,
            provider=provider,
            num_workers=num_workers,
        )

        unified_result.update(index.file_to_symbols)

    return unified_result


def _build_language_symbol_table(
    file_paths: list[Path], project_root: Path, provider, num_workers: int | None = 8
) -> ReifiedProjectIndex:
    parser = provider.get_parser()
    resolver = provider.get_resolver()

    print("==> Parsing files...")

    parsed = ParsedProject.from_files(
        file_paths,
        project_root,
        parser=parser,
        num_workers=num_workers,
    )

    print("==> Resolving includes and visibility...")
    project_vis = ParsedProjectWithVisibility.from_parsed_project(
        parsed, resolver=resolver, num_workers=num_workers
    )

    print("==> Linking symbols...")
    linked = LinkedProject.from_parsed_project_with_visibility(
        project_vis, sep=provider.get_fqn_delimiter()
    )

    print("==> Reifying symbol graph...")
    return ReifiedProjectIndex.from_linked_project(
        linked, parsed.file_to_containment_map
    )
