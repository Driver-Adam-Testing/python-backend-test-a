from dataclasses import dataclass
from enum import StrEnum

import tree_sitter
from pydantic import ConfigDict

from utils.lang_specialization.symbol_common import (
    BespokeMarker,
    RawTreeSitterSymbolData,
    SymbolKind,
)
from utils.treesitter_drivers.base import DriverTree


class GoCallableKind(StrEnum):
    METHOD = "method"
    FUNCTION = "function"


class GoCallableData(BespokeMarker):
    kind: GoCallableKind
    ty_params: str | None
    rx_ty: str | None
    model_config = ConfigDict(frozen=True)


@dataclass
class GoDriverTree(DriverTree):
    language = "go"
    extensions = frozenset([".go"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        path_parts = []
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
                    more_indirection = True
                    while more_indirection:
                        for child in rx_ty.children:
                            if child.type == "pointer_type":
                                rx_ty = child
                                break
                        more_indirection = False
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
        else:
            parent = node.parent
            if parent.type == "source_file":
                path_parts.append(str(self.file_path.with_suffix("")))
            else:
                path_parts.append(
                    parent.child_by_field_name("name").text.decode("utf-8")
                )

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
        """
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
