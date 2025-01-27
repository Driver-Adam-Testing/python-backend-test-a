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

    # @abstractmethod
    # def extract_functions(self) -> List[tuple[tree_sitter.Node, str]]:
    #     pass
    #
    # @abstractmethod
    # def extract_data_structures(self) -> List[tuple[tree_sitter.Node, str]]:
    #     pass

    def get_node_line_range(self, node: tree_sitter.Node) -> tuple[int, int]:
        # TODO this behavior needs to be vetted further across kinds of nodes before it is used in production
        start_line = self.tree.root_node.start_point.row + node.start_point.row + 1
        end_line = self.tree.root_node.start_point.row + node.end_point.row + 1
        return start_line, end_line


def node_to_text(node: tree_sitter.Node) -> str:
    return node.text.decode("utf8")


class DriverTreeError(Exception):
    pass


class CDriverTree(DriverTree):
    language = "c"

    def extract_imports(self) -> list[tuple[tree_sitter.Node, str]]:
        query = self.tree_sitter_lang.query(
            textwrap.dedent(
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
        )
        matches = query.matches(self.tree.root_node)
        includes = []

        for match in matches:
            include_directive_node = match[1]["include_directive"][0]
            include_path_node = match[1]["include_path"][0]

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


if __name__ == "__main__":
    code = textwrap.dedent(
        """
        #include <stdio.h>
        #include "myheader.h"
        #include "../headers/another_header.h"
        #include    <stdlib.h>
        #  include "utils.h"
        #if defined(USE_CUSTOM_HEADER)
            #include "custom.h"
        #else
            #include <default.h>
        #endif

        int main(void) { return 1 }
        """
    )

    # with open(pathlib.Path(__file__).parent.resolve() / "basic_tests.c") as f:
    #     code = f.read()
    driver_tree = CDriverTree.from_code(code_str=code)

    includes = driver_tree.extract_imports()
    print("Extracted includes:")
    for include_node, text in includes:
        print("Line range:", driver_tree.get_node_line_range(include_node))
        print(include_node.text, text)
