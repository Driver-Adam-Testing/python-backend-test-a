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
        return []

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
