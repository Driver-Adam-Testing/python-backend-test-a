from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

import tree_sitter
import tree_sitter_c

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

LANGUAGES = {"c": tree_sitter.Language(tree_sitter_c.language())}


@dataclass
class DriverTree(ABC):
    """A Driver specific use of tree-sitter.

    DriverTree will be used to develop abstract syntax trees (ASTs) of single methods, code files, or entire repositories.
    Subclasses will implement language-specific behaviors such as extracting imports/includes.
    """

    tree_sitter_lang: tree_sitter.Language
    tree: tree_sitter.Tree
    # symbols: List[tree_sitter.Node]
    source_bytes: bytes
    language: str = ""

    @classmethod
    def from_code(cls, code_str: str) -> Self:
        if not cls.language:
            raise DriverTreeError(
                f"No language specified for {cls.__name__}. Override the 'language' attribute."
            )
        ts_lang = LANGUAGES[cls.language]
        parser = tree_sitter.Parser(ts_lang)
        source_bytes = bytes(code_str, "utf8")
        tree = parser.parse(source_bytes)
        return cls(
            tree=tree,
            tree_sitter_lang=ts_lang,
            source_bytes=source_bytes,
        )

    @abstractmethod
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_functions(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_data_structures(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        pass

    def get_node_line_range(self, node: tree_sitter.Node) -> tuple[int, int]:
        # Syntax nodes store their position in the source code both in raw bytes and row/column coordinates.
        # In a point, rows and columns are zero-based.
        # The row field represents the number of newlines before a given position
        # See: https://tree-sitter.github.io/tree-sitter/using-parsers/2-basic-parsing.html?highlight=row#syntax-nodes

        start_line = (
            self.tree.root_node.start_point.row + node.start_point.row + 1
        )  # Make it 1-based, as in editors
        end_line = self.tree.root_node.start_point.row + node.end_point.row + 1

        # Check if the last byte in the node's span is a newline; it seems sometimes the node includes it, so we adjust
        if self.source_bytes[node.end_byte - 1 : node.end_byte] == b"\n":
            end_line -= 1

        return start_line, end_line


def node_to_text(node: tree_sitter.Node) -> str:
    return node.text.decode("utf8")


class DriverTreeError(Exception):
    pass


def get_function_name_and_params(
    declarator_node: tree_sitter.Node,
) -> tuple[str | None, tree_sitter.Node | None]:
    """
    Extract the function name and parameter node from a function declarator.
    Handles attributes, nested declarators, and parenthesized declarators.
    """
    if declarator_node.type == "function_declarator":
        name_node = declarator_node.child_by_field_name("declarator")
        params_node = declarator_node.child_by_field_name("parameters")

        if name_node and name_node.type == "identifier":
            return name_node.text.decode("utf-8"), params_node
        elif name_node:
            # Recurse into nested declarators (e.g., parenthesized_declarator, pointer_declarator)
            return get_function_name_and_params(name_node)

    elif declarator_node.type in {
        "pointer_declarator",
        "parenthesized_declarator",
        "attributed_declarator",
    }:
        # Recurse into nested declarators
        inner_declarator = declarator_node.child_by_field_name("declarator")
        if inner_declarator:
            return get_function_name_and_params(inner_declarator)

    # Unsupported or unhandled declarator type
    return None, None


def find_identifier_node(node: tree_sitter.Node) -> tree_sitter.Node | None:
    """Recursively find the first identifier node in a declarator"""
    if node.type == "identifier":
        return node

    for child in node.children:
        if child.type == "identifier":
            return child
        result = find_identifier_node(child)
        if result:
            return result
    return None


class CDriverTree(DriverTree):
    language = "c"

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        """Extract all #include directives and their target text from the C code."""
        query = self.tree_sitter_lang.query(
            """
            (
              (preproc_include
                (string_literal) @include_path)
            ) @include_directive
            (
              (preproc_include
                (system_lib_string) @include_path)
            ) @include_directive
            """
        )
        matches = query.matches(self.tree.root_node)
        includes = []

        for _pattern_index, captures_by_name in matches:
            include_directive_node = captures_by_name["include_directive"][0]
            include_path_node = captures_by_name["include_path"][0]

            include_path_text = self.source_bytes[
                include_path_node.start_byte : include_path_node.end_byte
            ].decode()
            if include_path_node.type == "system_lib_string":
                include_path_text = include_path_text.replace("<", "").replace(">", "")
            elif include_path_node.type == "string_literal":
                include_path_text = include_path_text.replace('"', "")

            start_line, end_line = self.get_node_line_range(include_directive_node)
            includes.append(
                RawTreeSitterSymbolData(
                    name=include_path_text,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.IMPORT,
                )
            )
        sorted_includes = sorted(includes, key=lambda x: x.start_line)

        return sorted_includes

    def extract_functions(self) -> list[RawTreeSitterSymbolData]:
        query = self.tree_sitter_lang.query("(function_definition) @function_def")
        matches = query.matches(self.tree.root_node)
        functions = []

        for _pattern_index, captures_by_name in matches:
            function_def = captures_by_name["function_def"][0]
            declarator_node = function_def.child_by_field_name("declarator")
            func_name, params_node = get_function_name_and_params(declarator_node)
            if func_name is None:
                print("Could not parse function name for node:", declarator_node)
                func_name = None
            start_line, end_line = self.get_node_line_range(function_def)
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
            )
            functions.append(func)
        sorted_functions = sorted(functions, key=lambda x: x.start_line)
        return sorted_functions

    def extract_data_structures(self) -> list[RawTreeSitterSymbolData]:
        """
        Extract struct, union, and enum tags and typedefs, ignoring forward declarations.

        Note: we can mine the following tests for more cases to implement:
        https://github.com/tree-sitter/tree-sitter-c/blob/master/test/corpus/declarations.txt
        """

        query_str = """
        (
          [
            ; Typedef variants
            ;; struct typedef
            (type_definition
              type: (struct_specifier)
              declarator: (type_identifier) @struct.name
            ) @struct.typedef

            ;; union typedef
            (type_definition
              type: (union_specifier)
              declarator: (type_identifier) @union.name
            ) @union.typedef

            ;; enum typedef
            (type_definition
              type: (enum_specifier)
              declarator: (type_identifier) @enum.name
            ) @enum.typedef

            ; Direct declarations (wrapped in declaration)
            (declaration
              [
                (struct_specifier
                  (type_identifier)? @declared_struct.name
                  (field_declaration_list) @declared_struct.body
                ) @declared_struct.definition

                (union_specifier
                  (type_identifier)? @declared_union.name
                  (field_declaration_list) @declared_union.body
                ) @declared_union.definition

                (enum_specifier
                  (type_identifier)? @declared_enum.name
                  (enumerator_list) @declared_enum.body
                ) @declared_enum.definition
              ]
            )

            ; Bare specifiers (exclude in post-processing if they're inside a type_definition or declaration)
            (struct_specifier
              (type_identifier)? @struct.name
              (field_declaration_list) @struct.body
            ) @struct.definition

            (union_specifier
              (type_identifier)? @union.name
              (field_declaration_list) @union.body
            ) @union.definition

            (enum_specifier
              (type_identifier)? @enum.name
              (enumerator_list) @enum.body
            ) @enum.definition
          ]
        )
        """

        query = self.tree_sitter_lang.query(query_str)
        matches = query.matches(self.tree.root_node)
        results = []

        def has_ancestor(node: tree_sitter.Node, types: set) -> bool:
            """Check if node has any ancestor of given types."""
            parent = node.parent
            while parent:
                if parent.type in types:
                    return True
                parent = parent.parent
            return False

        for _pattern_idx, captures_dict in matches:
            match captures_dict:
                case {"struct.definition": [data_structure_node], **rest}:
                    # Skip bare struct/union/enum definitions inside type_definition or declaration
                    if has_ancestor(
                        data_structure_node, {"type_definition", "declaration"}
                    ):
                        continue
                    name_nodes = rest.get("struct.name", [])
                case {"union.definition": [data_structure_node], **rest}:
                    # Skip bare struct/union/enum definitions inside type_definition or declaration
                    if has_ancestor(
                        data_structure_node, {"type_definition", "declaration"}
                    ):
                        continue
                    name_nodes = rest.get("union.name", [])
                case {"enum.definition": [data_structure_node], **rest}:
                    # Skip bare struct/union/enum definitions inside type_definition or declaration
                    if has_ancestor(
                        data_structure_node, {"type_definition", "declaration"}
                    ):
                        continue
                    name_nodes = rest.get("enum.name", [])
                case {"declared_struct.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("declared_struct.name", [])
                case {"declared_union.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("declared_union.name", [])
                case {"declared_enum.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("declared_enum.name", [])
                case {"struct.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("struct.name", [])
                case {"union.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("union.name", [])
                case {"enum.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("enum.name", [])
                case _:
                    raise DriverTreeError("Unexpected case in extract_data_structures")

            # Convert the name node (if any) into text; note we assume a single type, but typedefs could
            # actually declare multiple. There's a test case that shows it. < TODO
            if len(name_nodes) > 0:
                name_node = name_nodes[0]
                data_structure_name = self.source_bytes[
                    name_node.start_byte : name_node.end_byte
                ].decode("utf8")
            else:
                data_structure_name = None  # If we didn't capture a name...

            start_line, end_line = self.get_node_line_range(data_structure_node)
            ds = RawTreeSitterSymbolData(
                name=data_structure_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.DATA_STRUCTURE,
            )
            results.append(ds)

        results.sort(key=lambda x: x.start_line)
        return results

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        query = self.tree_sitter_lang.query(
            """
            (declaration) @global_var
            """
        )
        matches = query.matches(self.tree.root_node)

        def is_top_level_or_preprocessor_wrapped(node: tree_sitter.Node) -> bool:
            """
            Returns True if the node is under translation_unit (top level)
            with only preprocessor nodes in between.
            """
            parent = node.parent
            while parent:
                if parent.type == "translation_unit":
                    return True
                if not parent.type.startswith("preproc_"):
                    return False  # If there's a non-preprocessor ancestor before translation_unit, it's not global
                parent = parent.parent
            return False

        variables = []
        for _pattern_index, captures_by_name in matches:
            decl_node = captures_by_name["global_var"][0]

            if not is_top_level_or_preprocessor_wrapped(decl_node):
                continue

            start_line, end_line = self.get_node_line_range(decl_node)

            if any(child.type == "function_declarator" for child in decl_node.children):
                continue
            if any(child.type == "type_definition" for child in decl_node.children):
                continue

            # Find the identifier node(s) in this declaration
            for child in decl_node.children:
                if child.type in [
                    "identifier",
                    "init_declarator",
                    "pointer_declarator",
                    "array_declarator",
                    "attributed_declarator",
                ]:
                    id_node = find_identifier_node(child)
                    if id_node:
                        var_name = id_node.text.decode("utf8")
                        var = RawTreeSitterSymbolData(
                            name=var_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.VARIABLE,
                        )
                        variables.append(var)

        sorted_vars = sorted(variables, key=lambda x: x.start_line)
        return sorted_vars


if __name__ == "__main__":
    """
    Test code; left with a known case our code does not fully handle yet so you can
    implement it!
    """

    code = """typedef struct {
    int x;
    int y;
}
Point2, *Point2Ptr;
"""
    driver_tree = CDriverTree.from_code(code)
    data_structures = driver_tree.extract_data_structures()
    print(driver_tree.tree.root_node.children)
    print(data_structures)
