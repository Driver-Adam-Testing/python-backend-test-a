import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

import tree_sitter
import tree_sitter_c

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
    def extract_imports(self) -> list[tuple[tree_sitter.Node, str]]:
        pass

    @abstractmethod
    def extract_functions(self) -> list[tuple[tree_sitter.Node, str]]:
        pass

    @abstractmethod
    def extract_data_structures(self) -> list[tuple[tree_sitter.Node, str]]:
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


class CDriverTree(DriverTree):
    language = "c"

    def extract_imports(self) -> list[tuple[tree_sitter.Node, str]]:
        """Extract all #include directives and their target text from the C code."""
        query = self.tree_sitter_lang.query(
            textwrap.dedent("""
            (
              (preproc_include
                (string_literal) @include_path)
            ) @include_directive
            (
              (preproc_include
                (system_lib_string) @include_path)
            ) @include_directive
            """)
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

            includes.append((include_directive_node, include_path_text))
        sorted_includes = sorted(includes, key=lambda x: x[0].start_byte)
        return sorted_includes

    def extract_functions(self) -> list[tuple[tree_sitter.Node, str]]:
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
            functions.append((function_def, func_name))
        return functions

    def extract_data_structures(self) -> list[tuple[tree_sitter.Node, str | None]]:
        """
        Extract struct, union, and enum tags and typedefs, ignoring forward declarations.
        Note the usage of 'translation_unit' to ensure we only match top-level declarations and so that we don't
        double-count typedefs that have a struct (or other kind of tag) within them.
        """

        query_str = textwrap.dedent("""
          ; Match the struct, union, and enum tags...
          (translation_unit
            (struct_specifier
              (type_identifier)? @struct.name
              (field_declaration_list) @struct.body
            ) @struct.definition
          )

          (translation_unit
            (union_specifier
              (type_identifier)? @union.name
              (field_declaration_list) @union.body
            ) @union.definition
          )

          (translation_unit
            (enum_specifier
              (type_identifier)? @enum.name
              (enumerator_list) @enum.body
            ) @enum.definition
          )

          ; Match the struct, union, and enum tags that are combined with declarations..
          (declaration
              (struct_specifier
                (type_identifier)? @struct.name
                (field_declaration_list) @struct.body
              ) @struct.definition
            )

            (declaration
              (union_specifier
                (type_identifier)? @union.name
                (field_declaration_list) @union.body
              ) @union.definition
            )

            (declaration
              (enum_specifier
                (type_identifier)? @enum.name
                (enumerator_list) @enum.body
              ) @enum.definition
            )

          ; Now capture the typedef variants...
          (translation_unit
            (type_definition
              type: (struct_specifier)
              declarator: (type_identifier) @struct.name
            ) @struct.typedef
          )

          (translation_unit
            (type_definition
              type: (union_specifier)
              declarator: (type_identifier) @union.name
            ) @union.typedef
          )

          (translation_unit
            (type_definition
              type: (enum_specifier)
              declarator: (type_identifier) @enum.name
            ) @enum.typedef
          )
        """)

        query = self.tree_sitter_lang.query(query_str)
        matches = query.matches(self.tree.root_node)
        results = []

        for _pattern_idx, captures_dict in matches:
            match captures_dict:
                case {"struct.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("struct.name", [])
                case {"union.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("union.name", [])
                case {"enum.definition": [data_structure_node], **rest}:
                    name_nodes = rest.get("enum.name", [])
                case {"struct.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("struct.name", [])
                case {"union.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("union.name", [])
                case {"enum.typedef": [data_structure_node], **rest}:
                    name_nodes = rest.get("enum.name", [])
                case _:
                    raise DriverTreeError("Unexpected case in extract_data_structures")

            # Convert the name node (if any) into text
            if len(name_nodes) > 0:
                name_node = name_nodes[0]
                data_structure_name = self.source_bytes[
                    name_node.start_byte : name_node.end_byte
                ].decode("utf8")
            else:
                data_structure_name = None  # If we didn't capture a name...

            results.append((data_structure_node, data_structure_name))

        results.sort(key=lambda x: x[0].start_byte)
        return results


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
