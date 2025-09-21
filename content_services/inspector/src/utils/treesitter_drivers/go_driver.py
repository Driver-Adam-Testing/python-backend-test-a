from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import tree_sitter
from pydantic import ConfigDict

from utils.lang_specialization.symbol_common import (
    BespokeMarker,
    RawTreeSitterSymbolData,
    SymbolKind,
)
from utils.treesitter_drivers.base import DriverTree


def _is_exported(name: str) -> bool:
    return name and name[0].isupper()


class GoCallableKind(StrEnum):
    METHOD = "method"
    FUNCTION = "function"


class GoCallableData(BespokeMarker):
    kind: GoCallableKind
    is_exported: bool
    ty_params: str | None
    rx_ty: str | None
    model_config = ConfigDict(frozen=True)


class GoImportData(BespokeMarker):
    package_path: str
    package_alias: str | None
    dot_import: bool
    blank_import: bool


@dataclass
class GoDriverTree(DriverTree):
    language = "go"
    extensions = frozenset([".go"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        path_parts = []
        current = node.parent

        # TODO: Should we do this? Or just let the association with the
        # TODO: receiver type be made via link/soft description?
        # Special case methods to associate their receiver as a parent
        if node.type == "method_declaration":
            # TODO, how to handle poineters?
            rx = node.child_by_field_name("receiver")
            param_decl = None
            for child in rx.children:
                if child.type == "parameter_declaration":
                    param_decl = child
                    break
            if param_decl:
                rx_ty = param_decl.child_by_field_name("type")
                # Handle *Type (or arbitrary pointer indirection)
                if rx_ty.type == "pointer_type":
                    for child in rx_ty.children:
                        if child.type == "type_identifier":
                            path_parts.append(child.text.decode("utf-8"))
                            break
                elif rx_ty.type == "type_identifier":
                    path_parts.append(rx_ty.text.decode("utf-8"))
                else:
                    # TODO: this really should be unreachable
                    path_parts.append("")
            else:
                # TODO: handle this better
                path_parts.append("")

        while current:
            if current.type == "source_file":
                for child in current.children:
                    if child.type == "package_clause":
                        for grandchild in child.children:
                            if grandchild.type == "package_identifier":
                                path_parts.append(grandchild.text.decode("utf-8"))
                break
            # TODO: Should this be qualified/constrained?
            elif current.child_by_field_name("name"):
                path_parts.append(
                    current.child_by_field_name("name").text.decode("utf-8")
                )
            current = current.parent

        path_parts.reverse()
        return sep.join(path_parts)

    def node_to_text(self, node: tree_sitter.Node) -> str:
        start = node.start_byte
        end = node.end_byte

        return self.source_bytes[start:end].decode("utf-8")

    def _make_symbol(
        self,
        name: str,
        node: tree_sitter.Node,
        symbol_kind: SymbolKind,
        bespoke_data: BespokeMarker,
        delimiter: str = ".",
    ) -> RawTreeSitterSymbolData:
        start_line, end_line = self.get_node_line_range(node=node)
        fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(node)
        print(f"FQPP for {name}: {fully_qualified_parent_path}")

        return RawTreeSitterSymbolData(
            name=name,
            start_line=start_line,
            end_line=end_line,
            symbol_kind=symbol_kind,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            file_path=self.file_path,
            fully_qualified_parent_path=fully_qualified_parent_path,
            symbol_code=self.node_to_text(node=node),
            delimiter=delimiter,
            bespoke_data=bespoke_data,
        )

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = """
(import_declaration
  (import_spec) @import_spec) @import_decl

(import_declaration
  (import_spec_list (import_spec) @import_spec)) @import_decl
        """.strip()
        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, import_query_str)
        )
        import_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            import_node = captures_by_name.get("import_decl")[0]
            spec = captures_by_name.get("import_spec")[0]
            package_path = (spec.child_by_field_name("path").text.decode("utf-8"))[1:-1]
            name_node = spec.child_by_field_name("name")
            alias = None
            dot_import = False
            blank_import = False
            name = Path(package_path).name
            if name_node:
                if name_node.type == "package_identifier":
                    alias = name_node.text.decode("utf-8")
                    name = alias
                elif name_node.type == "dot":
                    dot_import = True
                elif name_node.type == "blank_identifier":
                    blank_import = True

            symbol_kind = SymbolKind.IMPORT
            bespoke_data = GoImportData(
                package_path=package_path,
                package_alias=alias,
                dot_import=dot_import,
                blank_import=blank_import,
            )

            if package_path and import_node:
                im = self._make_symbol(
                    name=name,
                    node=import_node,
                    symbol_kind=symbol_kind,
                    bespoke_data=bespoke_data,
                )
                import_list.append(im)
            else:
                print(
                    f"Missing package import path ({package_path}) or node ({import_node})"
                )

                # TODO: detect `defer`s.
        sorted_import_list = sorted(import_list, key=lambda x: x.start_byte)
        return sorted_import_list

        return []

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        free_fns = self.extract_function_definitions()
        methods = self.extract_method_definitions()
        return free_fns + methods

    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
        fn_query_str = """
(function_declaration
  name: (identifier) @fn_name
  type_parameters: (type_parameter_list)? @ty_params
) @fn_def
        """.strip()
        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, fn_query_str)
        )
        fn_list = []

        # TODO: Consider incorporating detection of `defer` statements and channels
        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            callable_name = captures_by_name.get("fn_name")[0].text.decode("utf-8")
            callable_node = captures_by_name.get("fn_def")[0]
            symbol_kind = SymbolKind.CALLABLE
            callable_kind = GoCallableKind.FUNCTION
            if callable_ty_params := captures_by_name.get("ty_params"):
                callable_ty_params = callable_ty_params[0].text.decode("utf-8")

            rx_ty = None
            bespoke_data = GoCallableData(
                kind=callable_kind,
                is_exported=_is_exported(callable_name),
                ty_params=callable_ty_params,
                rx_ty=rx_ty,
            )

            if callable_name and callable_node:
                fn = self._make_symbol(
                    name=callable_name,
                    node=callable_node,
                    symbol_kind=symbol_kind,
                    bespoke_data=bespoke_data,
                )
                fn_list.append(fn)
            else:
                print(
                    f"Missing function name ({callable_name}) or node ({callable_node})"
                )

                # TODO: detect `defer`s.
        sorted_fn_list = sorted(fn_list, key=lambda x: x.start_byte)
        return sorted_fn_list

    def extract_method_definitions(self) -> list[RawTreeSitterSymbolData]:
        method_query_str = """
(method_declaration
  receiver: (parameter_list
    (parameter_declaration
      name: (identifier)? @rx_name
      type: (_) @rx_ty
    )
  )
  name: (field_identifier) @method_name
  type_parameters: (type_parameter_list)? @ty_params
) @method_def
        """

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, method_query_str)
        )
        method_list = []

        # TODO: Consider incorporating detection of `defer` statements and channels
        # TODO: Consider identifying generic type parameters that aren't declared, if possible.
        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            callable_name = captures_by_name.get("method_name")[0].text.decode("utf-8")
            callable_node = captures_by_name.get("method_def")[0]
            symbol_kind = SymbolKind.CALLABLE
            callable_kind = GoCallableKind.METHOD
            if callable_ty_params := captures_by_name.get("ty_params"):
                callable_ty_params = callable_ty_params[0].text.decode("utf-8")

            rx_ty = captures_by_name.get("rx_ty")[0].text.decode("utf-8")
            bespoke_data = GoCallableData(
                kind=callable_kind,
                is_exported=_is_exported(callable_name),
                ty_params=callable_ty_params,
                rx_ty=rx_ty,
            )

            if callable_name and callable_node:
                method = self._make_symbol(
                    name=callable_name,
                    node=callable_node,
                    symbol_kind=symbol_kind,
                    bespoke_data=bespoke_data,
                )
                method_list.append(method)
            else:
                print(
                    f"Missing method name ({callable_name}) or node ({callable_node})"
                )

                # TODO: detect `defer`s.
        sorted_method_list = sorted(method_list, key=lambda x: x.start_byte)
        return sorted_method_list
