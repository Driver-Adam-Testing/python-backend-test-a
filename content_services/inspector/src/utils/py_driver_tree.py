import tree_sitter

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind
from utils.treesitter_driver import DriverTree, node_to_text, symbol_extractor


def is_top_level_fn(node: tree_sitter.Node) -> bool:
    return node.parent and node.parent.type == "module"


def is_decorated_fn(node: tree_sitter.Node) -> bool:
    return node.parent and node.parent.type == "decorated_definition"


def get_function_name_and_params(
    fn_def_node: tree_sitter.Node,
) -> tuple[str | None, tree_sitter.Node]:
    if fn_def_node.type == "function_definition":
        name_node = fn_def_node.child_by_field_name("name")
        params_node = fn_def_node.child_by_field_name("parameters")

        if name_node is not None and name_node.type == "identifier":
            return name_node.text.decode("utf-8"), params_node

    return None, None


class PyDriverTree(DriverTree):
    language = "python"

    @symbol_extractor
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = """
        ;; Standard direct import
        (import_statement
          (dotted_name) @dotted_name_direct) @import_direct

        ;; Direct import with alias
        (import_statement
          (aliased_import
            name: (dotted_name) @aliased_name_direct
            alias: (identifier) @alias_name_direct)) @import_alias_direct

        ;; Import using `from`
        (import_from_statement
          (dotted_name) @dotted_name_from) @import_from

        ;; Imports from `future`
        (future_import_statement) @future_module
        """.strip()
        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for pat_idx, captures_by_name in matches:
            match pat_idx:
                case 0:  # Direct imports
                    if captures_by_name.get("import_direct") and captures_by_name.get(
                        "dotted_name_direct"
                    ):
                        im_node = captures_by_name["import_direct"][0]
                        im_name = captures_by_name["dotted_name_direct"][0].text.decode(
                            "utf-8"
                        )
                        start_line, end_line = self.get_node_line_range(im_node)
                        im = RawTreeSitterSymbolData(
                            name=im_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.IMPORT,
                            start_byte=im_node.start_byte,
                            end_byte=im_node.end_byte,
                            file_path=self.file_path,
                            symbol_code=node_to_text(im_node),
                        )
                        imports.append(im)
                case 1:  # Direct imports with aliases
                    if captures_by_name.get(
                        "import_alias_direct"
                    ) and captures_by_name.get("aliased_name_direct"):
                        im_node = captures_by_name["import_alias_direct"][0]
                        im_name = captures_by_name["aliased_name_direct"][
                            0
                        ].text.decode("utf-8")
                        start_line, end_line = self.get_node_line_range(im_node)
                        im = RawTreeSitterSymbolData(
                            name=im_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.IMPORT,
                            start_byte=im_node.start_byte,
                            end_byte=im_node.end_byte,
                            file_path=self.file_path,
                            symbol_code=node_to_text(im_node),
                        )
                        imports.append(im)
                case 2:  # All from x import y
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
                                symbol_code=node_to_text(im_node),
                            )
                            imports.append(im)
                case 3:  # `__future__` imports
                    if captures_by_name.get("future_module"):
                        im_node = captures_by_name["future_module"][0]
                        start_line, end_line = self.get_node_line_range(im_node)
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
                                symbol_code=node_to_text(im_node),
                            )
                            imports.append(im)
                case _:
                    print(f"Could not parse import for capture: {captures_by_name}")
                    continue

        sorted_imports = sorted(imports, key=lambda x: x.start_byte)
        return sorted_imports

    @symbol_extractor
    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
        fn_query_str = """
        ;; Free functions and methods
        (function_definition
          name: (identifier) @fn_name) @fn_def

        ;; Decorated free functions and methods
        (decorated_definition
          (function_definition
            name: (identifier) @fn_name) @fn_def)
        """.strip()
        query = self.tree_sitter_lang.query(fn_query_str)
        matches = query.matches(self.tree.root_node)
        functions = []

        for _pattern_index, captures_by_name in matches:
            fn_def_node = captures_by_name["fn_def"][0]
            if is_top_level_fn(fn_def_node) or is_decorated_fn(fn_def_node):
                fn_name, _params_node = get_function_name_and_params(
                    fn_def_node=fn_def_node
                )
                if fn_name is None:
                    print(f"Could not parse function name for node: {fn_def_node}")
                start_line, end_line = self.get_node_line_range(fn_def_node)
                # TODO: Consider detecting decorated functions and including the
                # TODO: decorator lines in the start_line/byte so that this information
                # TODO: is present downstream for LLMs looking at the source.
                fn = RawTreeSitterSymbolData(
                    name=fn_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.CALLABLE,
                    start_byte=fn_def_node.start_byte,
                    end_byte=fn_def_node.end_byte,
                    file_path=self.file_path,
                    symbol_code=node_to_text(fn_def_node),
                )
                functions.append(fn)
        sorted_functions = sorted(functions, key=lambda x: x.start_byte)
        return sorted_functions

    @symbol_extractor
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        raise NotImplementedError("Not relevant for Python")

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    @symbol_extractor
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return []

    @symbol_extractor
    def extract_classes(self) -> list[RawTreeSitterSymbolData]:
        return []
