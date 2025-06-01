from collections.abc import Callable

import tree_sitter

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.treesitter_driver import DriverTree, symbol_extractor


def py_node_to_text(source_bytes: bytes, node: tree_sitter.Node) -> str:
    start = node.start_byte
    end = node.end_byte

    # Walk backwdard to include semantically-meaningful leading indentation in Python.
    line_start = source_bytes.rfind(b"\n", 0, start) + 1
    return source_bytes[line_start:end].decode("utf-8")


def is_top_level_free_fn(node: tree_sitter.Node) -> bool:
    return node.parent and (
        node.parent.type == "module"
        or (
            node.parent.type == "decorated_definition"
            and node.parent.parent.type == "module"
        )
    )


def is_method(node: tree_sitter.Node) -> bool:
    return node.parent and (
        (node.parent.type == "block" and node.parent.parent.type == "class_definition")
        or (
            node.parent.type == "decorated_definition"
            and node.parent.parent.type == "block"
            and node.parent.parent.parent.type == "class_definition"
        )
    )


def get_callable_name_and_params(
    callable_def_node: tree_sitter.Node,
) -> tuple[str | None, tree_sitter.Node]:
    if callable_def_node.type == "function_definition":
        name_node = callable_def_node.child_by_field_name("name")
        params_node = callable_def_node.child_by_field_name("parameters")

        if name_node is not None and name_node.type == "identifier":
            return name_node.text.decode("utf-8"), params_node

    return None, None


class PyDriverTree(DriverTree):
    language = "python"

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "::"
    ) -> str:
        path_parts = []
        current = node.parent

        while current:
            # print(f"type: {current.type}, text: {current.text.decode('utf-8')}")
            if current.type == "module":
                path_parts.append(str(self.file_path.with_suffix("")))
            elif current.type in [
                "function_definition",
                "class_definition",
            ]:
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(name_node.text.decode("utf-8"))
            current = current.parent

        path_parts.reverse()
        return sep.join(path_parts) if path_parts else ""

    @symbol_extractor
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = """
        ;; All direct imports (with or without alias)
        (import_statement) @import_direct

        ;; Import using `from`
        (import_from_statement) @import_from

        ;; Imports from `future`
        (future_import_statement) @future_module
        """.strip()
        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for pat_idx, captures_by_name in matches:
            match pat_idx:
                case 0:  # All direct imports (with or without aliases)
                    if captures_by_name.get("import_direct"):
                        im_node = captures_by_name["import_direct"][0]
                        start_line, end_line = self.get_node_line_range(im_node)
                        fully_qualified_parent_path = (
                            self._get_fully_qualified_path_to_parent(node=im_node)
                        )

                        # Handle different types of direct imports by examining child nodes
                        for child in im_node.named_children:
                            if child.type == "aliased_import":
                                # Direct import with alias: import numpy as np
                                name_node = child.child_by_field_name("name")
                                if name_node:
                                    im_name = name_node.text.decode("utf-8")
                                    im = RawTreeSitterSymbolData(
                                        name=im_name,
                                        start_line=start_line,
                                        end_line=end_line,
                                        symbol_kind=SymbolKind.IMPORT,
                                        start_byte=im_node.start_byte,
                                        end_byte=im_node.end_byte,
                                        file_path=self.file_path,
                                        fully_qualified_parent_path=fully_qualified_parent_path,
                                        symbol_code=py_node_to_text(
                                            self.source_bytes, im_node
                                        ),
                                    )
                                    imports.append(im)
                            elif child.type == "dotted_name":
                                # Direct import without alias: import os
                                im_name = child.text.decode("utf-8")
                                im = RawTreeSitterSymbolData(
                                    name=im_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    symbol_kind=SymbolKind.IMPORT,
                                    start_byte=im_node.start_byte,
                                    end_byte=im_node.end_byte,
                                    file_path=self.file_path,
                                    fully_qualified_parent_path=fully_qualified_parent_path,
                                    symbol_code=py_node_to_text(
                                        self.source_bytes, im_node
                                    ),
                                )
                                imports.append(im)
                case 1:  # All from x import y
                    if captures_by_name.get("import_from"):
                        im_node = captures_by_name["import_from"][0]
                        children = im_node.named_children
                        from_module = children[0].text.decode("utf-8")
                        sep = (
                            ""
                            if children[0].type == "relative_import"
                            and all(c == "." for c in from_module)
                            else "."
                        )
                        start_line, end_line = self.get_node_line_range(im_node)
                        fully_qualified_parent_path = (
                            self._get_fully_qualified_path_to_parent(node=im_node)
                        )
                        for child in children[1:]:
                            if child.type == "dotted_name":
                                im_name = sep.join(
                                    [from_module, child.text.decode("utf-8")]
                                )
                            elif child.type == "aliased_import":
                                im_name = sep.join(
                                    [
                                        from_module,
                                        child.child_by_field_name("name").text.decode(
                                            "utf-8"
                                        ),
                                    ]
                                )
                            elif child.type == "wildcard_import":
                                im_name = sep.join([from_module, "*"])
                            else:
                                print("Could not parse import for node: {im_node}")
                                continue
                            im = RawTreeSitterSymbolData(
                                name=im_name,
                                start_line=start_line,
                                end_line=end_line,
                                symbol_kind=SymbolKind.IMPORT,
                                start_byte=im_node.start_byte,
                                end_byte=im_node.end_byte,
                                file_path=self.file_path,
                                fully_qualified_parent_path=fully_qualified_parent_path,
                                symbol_code=py_node_to_text(self.source_bytes, im_node),
                            )
                            imports.append(im)
                case 2:  # `__future__` imports
                    if captures_by_name.get("future_module"):
                        im_node = captures_by_name["future_module"][0]
                        start_line, end_line = self.get_node_line_range(im_node)
                        fully_qualified_parent_path = (
                            self._get_fully_qualified_path_to_parent(node=im_node)
                        )
                        print(fully_qualified_parent_path)
                        for child in im_node.named_children:
                            im_name = ".".join(
                                ["__future__", child.text.decode("utf-8")]
                            )
                            im = RawTreeSitterSymbolData(
                                name=im_name,
                                start_line=start_line,
                                end_line=end_line,
                                symbol_kind=SymbolKind.IMPORT,
                                start_byte=im_node.start_byte,
                                end_byte=im_node.end_byte,
                                file_path=self.file_path,
                                fully_qualified_parent_path=fully_qualified_parent_path,
                                symbol_code=py_node_to_text(self.source_bytes, im_node),
                            )
                            imports.append(im)
                case _:
                    print(f"Could not parse import for capture: {captures_by_name}")
                    continue

        sorted_imports = sorted(imports, key=lambda x: x.start_byte)
        return sorted_imports

    @symbol_extractor
    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        free_fns = self.extract_function_definitions()
        methods = self.extract_method_definitions()
        return free_fns + methods

    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
        return self._extract_callable_definitions_by_kind(kind_fn=is_top_level_free_fn)

    def extract_method_definitions(self) -> list[RawTreeSitterSymbolData]:
        return self._extract_callable_definitions_by_kind(kind_fn=is_method)

    def _extract_callable_definitions_by_kind(
        self, kind_fn: Callable[[tree_sitter.Node], bool]
    ) -> list[RawTreeSitterSymbolData]:
        callable_query_str = """
        ;; All callables -- free functions and methods
        (function_definition
          name: (identifier) @callable_name) @callable_def
        """.strip()
        query = self.tree_sitter_lang.query(callable_query_str)
        matches = query.matches(self.tree.root_node)
        callables = []

        for _pattern_index, captures_by_name in matches:
            callable_def_node = captures_by_name["callable_def"][0]
            if kind_fn(callable_def_node):
                callable_name, _params_node = get_callable_name_and_params(
                    callable_def_node=callable_def_node
                )
                if callable_name is None:
                    print(
                        f"Could not parse function name for node: {callable_def_node}"
                    )
                start_line, end_line = self.get_node_line_range(callable_def_node)
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    node=callable_def_node
                )
                if callable_def_node.parent.type == "decorated_definition":
                    start_line, end_line = self.get_node_line_range(
                        callable_def_node.parent
                    )
                    start_byte, end_byte = (
                        callable_def_node.parent.start_byte,
                        callable_def_node.parent.end_byte,
                    )
                    symbol_code = py_node_to_text(
                        source_bytes=self.source_bytes, node=callable_def_node.parent
                    )
                else:
                    start_line, end_line = self.get_node_line_range(callable_def_node)
                    start_byte, end_byte = (
                        callable_def_node.start_byte,
                        callable_def_node.end_byte,
                    )
                    symbol_code = py_node_to_text(
                        source_bytes=self.source_bytes, node=callable_def_node
                    )
                fn_like = RawTreeSitterSymbolData(
                    name=callable_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.CALLABLE,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    file_path=self.file_path,
                    fully_qualified_parent_path=fully_qualified_parent_path,
                    symbol_code=symbol_code,
                )
                callables.append(fn_like)
        sorted_callables = sorted(callables, key=lambda x: x.start_byte)
        return sorted_callables

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        raise NotImplementedError("Not relevant for Python")

    @symbol_extractor
    def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
        klass_query_str = """
        (class_definition
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
            if klass_node.child_by_field_name("superclasses"):
                base_class_names = []
                for bc in klass_node.child_by_field_name("superclasses").children:
                    if bc.type == "identifier":
                        base_class_names.append(bc.text.decode("utf-8"))
            else:
                base_class_names = None
            if klass_node.parent.type == "decorated_definition":
                start_line, end_line = self.get_node_line_range(klass_node.parent)
                start_byte, end_byte = (
                    klass_node.parent.start_byte,
                    klass_node.parent.end_byte,
                )
                symbol_code = py_node_to_text(self.source_bytes, klass_node.parent)
            else:
                start_line, end_line = self.get_node_line_range(klass_node)
                start_byte, end_byte = klass_node.start_byte, klass_node.end_byte
                symbol_code = py_node_to_text(self.source_bytes, klass_node)
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
                fully_qualified_parent_path=fully_qualified_parent_path,
                base_class_names=base_class_names,
                symbol_code=symbol_code,
            )
            klasses.append(klass)

        sorted_klasses = sorted(klasses, key=lambda x: x.start_byte)
        return sorted_klasses

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    @symbol_extractor
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        global_var_query_str = """
        ;; Single variable assignment
        (module
          (expression_statement
            (assignment
              left: (identifier) @global_name)) @global_expression)

        ;; Multiple assignment / tuple unpacking
        (module
          (expression_statement
            (assignment
              left: (pattern_list
                (identifier) @global_name)) @global_expression))
        """.strip()
        query = self.tree_sitter_lang.query(global_var_query_str)
        matches = query.matches(self.tree.root_node)
        gbl_vars = []

        for pat_idx, captures_by_name in matches:
            gbl_expr_node = captures_by_name["global_expression"][0]
            if pat_idx == 0:  # Single assignment
                gbl_name = captures_by_name["global_name"][0]
                if gbl_name is None:
                    print(
                        f"Could not parse global variable name for node: {gbl_expr_node}"
                    )
                    continue
                else:
                    gbl_name = gbl_name.text.decode("utf-8")
                start_line, end_line = self.get_node_line_range(gbl_expr_node)
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    node=gbl_expr_node
                )

                gbl = RawTreeSitterSymbolData(
                    name=gbl_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.VARIABLE,
                    start_byte=gbl_expr_node.start_byte,
                    end_byte=gbl_expr_node.end_byte,
                    file_path=self.file_path,
                    fully_qualified_parent_path=fully_qualified_parent_path,
                    symbol_code=py_node_to_text(self.source_bytes, gbl_expr_node),
                )
                gbl_vars.append(gbl)
            elif pat_idx == 1:  # Multiple assignment
                # Handle all identifiers in the pattern_list
                for gbl_name_node in captures_by_name["global_name"]:
                    gbl_name = gbl_name_node.text.decode("utf-8")
                    start_line, end_line = self.get_node_line_range(gbl_expr_node)
                    fully_qualified_parent_path = (
                        self._get_fully_qualified_path_to_parent(node=gbl_expr_node)
                    )

                    gbl = RawTreeSitterSymbolData(
                        name=gbl_name,
                        start_line=start_line,
                        end_line=end_line,
                        symbol_kind=SymbolKind.VARIABLE,
                        start_byte=gbl_expr_node.start_byte,
                        end_byte=gbl_expr_node.end_byte,
                        file_path=self.file_path,
                        fully_qualified_parent_path=fully_qualified_parent_path,
                        symbol_code=py_node_to_text(self.source_bytes, gbl_expr_node),
                    )
                    gbl_vars.append(gbl)

        sorted_gbl_vars = sorted(gbl_vars, key=lambda x: x.start_byte)
        return sorted_gbl_vars
