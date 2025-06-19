from dataclasses import dataclass

import tree_sitter

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

from .base import DriverTree


def cs_node_to_text(source_bytes: bytes, node: tree_sitter.Node) -> str:
    start = node.start_byte
    end = node.end_byte

    return source_bytes[start:end].decode("utf-8")


def _extract_namespace_name(name_node: tree_sitter.Node, sep: str = ".") -> str:
    """Recursively extract full namespace name from a qualified_name node."""
    if name_node.type == "qualified_name":
        # Example: System.Collections.Generic
        parts = []
        for child in name_node.children:
            if child.type == "identifier":
                parts.append(child.text.decode("utf-8"))
        return sep.join(parts)
    elif name_node.type == "identifier":
        return name_node.text.decode("utf-8")
    return ""


@dataclass
class CSharpDriverTree(DriverTree):
    language = "csharp"
    extensions = frozenset([".cs"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        path_parts = []
        current = node.parent

        while current:
            if current.type == "compilation_unit":
                path_parts.append(str(self.file_path.with_suffix("")))
            elif current.type in {
                "class_declaration",
                "struct_declaration",
                "interface_declaration",
                "method_declaration",
            }:
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(name_node.text.decode("utf-8"))
            elif current.type == "namespace_declaration":
                # Namespace may be nested or qualified
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(
                        _extract_namespace_name(name_node=name_node, sep=sep)
                    )
            current = current.parent

        path_parts.reverse()
        return sep.join(path_parts)

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = "(using_directive) @using_stmt"
        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for _pat_idx, captures_by_name in matches:
            im_node = captures_by_name["using_stmt"][0]
            start_line, end_line = self.get_node_line_range(im_node)
            start_byte, end_byte = im_node.start_byte, im_node.end_byte
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                node=im_node
            )

            resolved_name = False
            # Handle easy signal -- presence of a qualified name
            if not resolved_name:
                for child in im_node.children:
                    if child.type == "qualified_name":
                        name = child.text.decode("utf-8")
                        resolved_name = True
                        break

            # Handle cases where a qualified name isn't present and presense of an alias
            # E.g., for `using System;` or `using Sys = System;`
            if not resolved_name:
                identifiers = []
                alias_used = False
                for child in im_node.children:
                    if child.type == "identifier":
                        identifiers.append(child.text.decode("utf-8"))
                        continue
                    if child.type == "=":
                        alias_used = True
                        identifiers.append("=")

                if alias_used:
                    split_idx = identifiers.index("=")
                    name = identifiers[split_idx + 1]
                    resolved_name = True
                else:
                    if len(identifiers) > 0:
                        name = identifiers[0]
                        resolved_name = True

            if not resolved_name:
                print(f"Unable to resolve import for {im_node.text.decode('utf-8')}")
                name = None

            im = RawTreeSitterSymbolData(
                name=name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.IMPORT,
                start_byte=start_byte,
                end_byte=end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=cs_node_to_text(self.source_bytes, im_node),
                delimiter=".",
            )
            imports.append(im)

        return imports

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
        klass_query_str = """
        (class_declaration
          name: (identifier) @class_name) @class_def
        """.strip()
        query = self.tree_sitter_lang.query(klass_query_str)
        matches = query.matches(self.tree.root_node)
        klasses = []

        for _pat_idx, captures_by_name in matches:
            klass_node = captures_by_name["class_def"][0]
            klass_name = captures_by_name["class_name"][0]
            if klass_name is None:
                print(f"Could not parse class name for node: {klass_node}")
            else:
                klass_name = klass_name.text.decode("utf-8")
            base_class_names = None
            for child in klass_node.children:
                if child.type == "base_list":
                    base_class_names = []
                    for base in child.children:
                        if base.type in {
                            "identifier",
                            "qualified_name",
                            "generic_name",
                            "invocation_expression",
                        }:
                            base_class_names.append(base.text.decode("utf-8"))
            start_line, end_line = self.get_node_line_range(klass_node)
            start_byte, end_byte = klass_node.start_byte, klass_node.end_byte
            symbol_code = cs_node_to_text(self.source_bytes, klass_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                node=klass_node
            )
            klass = RawTreeSitterSymbolData(
                name=klass_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CLASS,
                start_byte=start_byte,
                end_byte=end_byte,
                file_path=self.file_path,
                fully_qualified_path_to_parent=fully_qualified_parent_path,
                base_class_names=base_class_names,
                symbol_code=symbol_code,
                delimiter=".",
            )
            klasses.append(klass)

        sorted_klasses = sorted(klasses, key=lambda x: x.start_byte)
        return sorted_klasses
