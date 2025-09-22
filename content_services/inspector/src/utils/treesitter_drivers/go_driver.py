from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import tree_sitter
from pydantic import BaseModel, ConfigDict

from utils.lang_specialization.symbol_common import (
    BespokeMarker,
    RawTreeSitterSymbolData,
    SymbolKind,
)
from utils.treesitter_drivers.base import DriverTree


def _is_exported(name: str) -> bool:
    return name and name[0].isupper()


def _has_node_ty(const_decl_node: tree_sitter.Node, ty: str) -> bool:
    def find_ty_recursive(node: tree_sitter.Node, ty: str) -> bool:
        if node.type == ty:
            return True

        return any(find_ty_recursive(node=child, ty=ty) for child in node.children)

    return find_ty_recursive(node=const_decl_node, ty=ty)


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


class GoDataStructureKind(StrEnum):
    STRUCT = "struct"
    EMPTY_STRUCT = "empty_struct"
    TYPE_ALIAS = "type_alias"
    NEW_TYPE = "new_type"


class GoDataStructureData(BespokeMarker):
    kind: GoDataStructureKind
    is_exported: bool
    ty_params: str | None
    model_config = ConfigDict(frozen=True)


class GoGlobalKind(StrEnum):
    GLOBAL_VAR = "global_var"
    GLOBAL_VAR_GROUP = "global_var_group"
    GLOBAL_CONST = "global_const"
    GLOBAL_CONST_GROUP = "global_const_group"


class GoSingleGlobal(BaseModel):
    name: str
    is_exported: bool
    # model_config = ConfigDict(frozen=True)


class GoGlobalData(BespokeMarker):
    kind: GoGlobalKind
    components: list[GoSingleGlobal]
    uses_iota: bool
    model_config = ConfigDict(frozen=True)


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
        data_structure_query_str = """
(type_declaration
  (type_spec
    name: (type_identifier) @ty_name
    type_parameters: (type_parameter_list)? @ty_params
    type: (_) @ty_def)) @ty_decl

(type_declaration
  (type_alias
    name: (type_identifier) @ty_name
    type: (_) @ty_def)) @ty_decl
        """.strip()
        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, data_structure_query_str)
        )
        data_structure_list = []

        for pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            data_structure_node = captures_by_name.get("ty_decl")[0]
            data_structure_name = captures_by_name.get("ty_name")[0].text.decode(
                "utf-8"
            )
            data_structure_definition = captures_by_name.get("ty_def")[0]
            symbol_kind = SymbolKind.DATA_STRUCTURE
            data_structure_ty_params = None
            match pattern_idx:
                case 0:  # `struct`s and new types
                    if data_structure_ty_params := captures_by_name.get("ty_params"):
                        data_structure_ty_params = data_structure_ty_params[
                            0
                        ].text.decode("utf-8")
                    if data_structure_definition.type == "struct_type":
                        data_structure_kind = GoDataStructureKind.EMPTY_STRUCT
                        for child in data_structure_definition.children:
                            if child.type == "field_declaration_list":
                                for grandchild in child.children:
                                    if grandchild.type == "field_declaration":
                                        data_structure_kind = GoDataStructureKind.STRUCT
                                        break
                                else:
                                    continue
                                break
                    else:
                        data_structure_kind = GoDataStructureKind.NEW_TYPE
                case 1:  # type aliases
                    data_structure_kind = GoDataStructureKind.TYPE_ALIAS
                case _:
                    raise ValueError("Unreachable")

            bespoke_data = GoDataStructureData(
                kind=data_structure_kind,
                is_exported=_is_exported(name=data_structure_name),
                ty_params=data_structure_ty_params,
            )

            if data_structure_name and data_structure_node:
                data_structure = self._make_symbol(
                    name=data_structure_name,
                    node=data_structure_node,
                    symbol_kind=symbol_kind,
                    bespoke_data=bespoke_data,
                )
                data_structure_list.append(data_structure)
            else:
                print(
                    f"Missing data structure name ({data_structure_name}) or node ({data_structure_node})"
                )

        sorted_data_structure_list = sorted(
            data_structure_list, key=lambda x: x.start_byte
        )
        return sorted_data_structure_list

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_package_globals(self) -> list[RawTreeSitterSymbolData]:
        globals_query_str = """
(source_file
  (var_declaration) @package_var_decl)

(source_file
  (const_declaration) @package_const_decl)
        """.strip()
        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, globals_query_str)
        )
        globals_list = []

        for pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            match pattern_idx:
                case 0:  # global vars
                    global_node = captures_by_name.get("package_var_decl")[0]
                    uses_iota = False
                    var_decl_data = []
                    for child in global_node.children:
                        if child.type == "var_spec":  # single var declaration
                            name = child.child_by_field_name("name").text.decode(
                                "utf-8"
                            )
                            is_exported = _is_exported(name=name)
                            var_decl_data.append(
                                GoSingleGlobal(name=name, is_exported=is_exported)
                            )
                            break
                        if child.type == "var_spec_list":  # var group
                            for var in child.children:
                                if var.type == "var_spec":
                                    name = var.child_by_field_name("name").text.decode(
                                        "utf-8"
                                    )
                                    is_exported = _is_exported(name=name)
                                    var_decl_data.append(
                                        GoSingleGlobal(
                                            name=name, is_exported=is_exported
                                        )
                                    )
                            break
                    kind = (
                        GoGlobalKind.GLOBAL_VAR_GROUP
                        if len(var_decl_data) > 1
                        else GoGlobalKind.GLOBAL_VAR
                    )
                    if global_node:
                        globals_list.append(
                            self._make_symbol(
                                name="package_variable_declaration",
                                node=global_node,
                                symbol_kind=SymbolKind.VARIABLE,
                                bespoke_data=GoGlobalData(
                                    kind=kind,
                                    components=var_decl_data,
                                    uses_iota=uses_iota,
                                ),
                            )
                        )
                    else:
                        print(f"Missing node ({global_node})")
                case 1:  # global constants
                    global_node = captures_by_name.get("package_const_decl")[0]
                    uses_iota = _has_node_ty(const_decl_node=global_node, ty="iota")
                    const_decl_data = []
                    for child in global_node.children:
                        if child.type == "const_spec":
                            name = child.child_by_field_name("name").text.decode(
                                "utf-8"
                            )
                            is_exported = _is_exported(name=name)
                            const_decl_data.append(
                                GoSingleGlobal(name=name, is_exported=is_exported)
                            )
                    kind = (
                        GoGlobalKind.GLOBAL_CONST_GROUP
                        if len(const_decl_data) > 1
                        else GoGlobalKind.GLOBAL_CONST
                    )
                    if global_node:
                        globals_list.append(
                            self._make_symbol(
                                name="package_constant_declaration",
                                node=global_node,
                                symbol_kind=SymbolKind.VARIABLE,
                                bespoke_data=GoGlobalData(
                                    kind=kind,
                                    components=const_decl_data,
                                    uses_iota=uses_iota,
                                ),
                            )
                        )
                    else:
                        print(f"Missing node ({global_node})")
                case _:
                    raise ValueError("Unreachable")

        sorted_globals_list = sorted(globals_list, key=lambda x: x.start_byte)
        return sorted_globals_list

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return self.extract_package_globals()

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
