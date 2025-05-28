from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from inspect import getmembers, ismethod
from pathlib import Path
from typing import Self

import tree_sitter
import tree_sitter_c
import tree_sitter_cpp

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

LANGUAGES = {
    "c": tree_sitter.Language(tree_sitter_c.language()),
    "cpp": tree_sitter.Language(tree_sitter_cpp.language()),
}


def symbol_extractor(
    method: Callable[..., list[RawTreeSitterSymbolData]],
) -> Callable[..., list[RawTreeSitterSymbolData]]:
    method._is_symbol_extractor = True
    return method


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
    file_path: Path
    language: str = ""

    @classmethod
    def from_code(cls, code_str: str, file_path: Path | str) -> Self:
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
            file_path=Path(file_path),
        )

    @abstractmethod
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        pass

    # @abstractmethod
    # def extract_data_structure_instances(self) -> list[RawTreeSitterSymbolData]:
    #     pass

    @abstractmethod
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        pass

    def get_node_line_range(self, node: tree_sitter.Node) -> tuple[int, int]:
        """Returns the 1-based line range of a Tree-sitter node."""
        # Syntax nodes store their position in the source code both in raw bytes and row/column coordinates.
        # In a point (row, column), rows and columns are zero-based.
        # The row field represents the number of newlines before a given position, while the column is the byte offset
        # from the start of the row.
        # See: https://tree-sitter.github.io/tree-sitter/using-parsers/2-basic-parsing.html?highlight=row#syntax-nodes

        start_line = node.start_point.row + 1  # Convert 0-based row to 1-based
        end_line = node.end_point.row + 1

        # Check if the last byte in the node's span is a newline; adjust if needed
        if self.source_bytes[node.end_byte - 1 : node.end_byte] == b"\n":
            end_line -= 1

        return start_line, end_line

    def extract_all_symbols(self) -> list[RawTreeSitterSymbolData]:
        all_symbols: list[RawTreeSitterSymbolData] = []

        for _, method in getmembers(self, predicate=ismethod):
            if getattr(method, "_is_symbol_extractor", False):
                try:
                    all_symbols.extend(method())
                except NotImplementedError:
                    continue

        return sorted(all_symbols, key=lambda s: s.start_line)


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

    @symbol_extractor
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
            ts_node = include_path_node
            includes.append(
                RawTreeSitterSymbolData(
                    name=include_path_text,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.IMPORT,
                    start_byte=ts_node.start_byte,
                    end_byte=ts_node.end_byte,
                    file_path=self.file_path,
                    symbol_code=node_to_text(ts_node),
                )
            )
        sorted_includes = sorted(includes, key=lambda x: x.start_byte)

        return sorted_includes

    @symbol_extractor
    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
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
            ts_node = function_def
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )
            functions.append(func)
        sorted_functions = sorted(functions, key=lambda x: x.start_byte)
        return sorted_functions

    @symbol_extractor
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
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
            ts_node = data_structure_node
            ds = RawTreeSitterSymbolData(
                name=data_structure_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.DATA_STRUCTURE,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )

            results.append(ds)

        results.sort(key=lambda x: x.start_byte)
        return results

    @symbol_extractor
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
                        ts_node = decl_node
                        var = RawTreeSitterSymbolData(
                            name=var_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.VARIABLE,
                            start_byte=ts_node.start_byte,
                            end_byte=ts_node.end_byte,
                            file_path=self.file_path,
                            symbol_code=node_to_text(ts_node),
                        )
                        variables.append(var)

        sorted_vars = sorted(variables, key=lambda x: x.start_byte)
        return sorted_vars

    # TODO we really need to swap to byte position since we often have
    # multiple calls per line to disambiguate

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        query = self.tree_sitter_lang.query("(call_expression) @call")
        matches = query.matches(self.tree.root_node)
        function_calls = []

        for _pattern_index, captures_by_name in matches:
            call_node = captures_by_name["call"][0]

            # Extract function name (identifier within call_expression)
            identifier_node = call_node.child_by_field_name("function")
            if identifier_node is None or identifier_node.type != "identifier":
                continue  # Skip if we can't find a valid function name

            func_name = identifier_node.text.decode("utf-8")

            start_line, end_line = self.get_node_line_range(call_node)
            ts_node = call_node
            func_call = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALL,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )

            function_calls.append(func_call)

        # Sort the calls by their start byte
        sorted_calls = sorted(function_calls, key=lambda x: x.start_byte)
        return sorted_calls

    # def extract_data_structure_instances(self) -> list[RawTreeSitterSymbolData]:
    #     pass

    @symbol_extractor
    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        """Extract all function declarations (not definitions) in the C code."""
        query = self.tree_sitter_lang.query("(declaration) @declaration")
        matches = query.matches(self.tree.root_node)
        declarations = []

        for _pattern_index, captures_by_name in matches:
            declaration_node = captures_by_name["declaration"][0]

            declarator_node = declaration_node.child_by_field_name("declarator")
            if not declarator_node:
                continue

            # Ensure it's a function declarator implicitly by calling this and having it return something
            func_name, params_node = get_function_name_and_params(declarator_node)
            if func_name is None:
                continue

            # Function declaration should not have a body
            has_body = any(
                child.type == "compound_statement"
                for child in declaration_node.children
            )
            if has_body:
                continue

            start_line, end_line = self.get_node_line_range(declaration_node)
            ts_node = declaration_node
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE_DECLARATION,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )
            declarations.append(func)

        sorted_declarations = sorted(declarations, key=lambda x: x.start_byte)
        return sorted_declarations


class CppDriverTree(DriverTree):
    language = "cpp"

    @symbol_extractor
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        """Extract all #include directives and their target text from the C++ code."""
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
            ts_node = include_path_node
            includes.append(
                RawTreeSitterSymbolData(
                    name=include_path_text,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.IMPORT,
                    start_byte=ts_node.start_byte,
                    end_byte=ts_node.end_byte,
                    file_path=self.file_path,
                    symbol_code=node_to_text(ts_node),
                )
            )
        sorted_includes = sorted(includes, key=lambda x: x.start_byte)
        return sorted_includes

    @symbol_extractor
    def extract_function_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract function definitions including methods, constructors, destructors, and operators."""
        query = self.tree_sitter_lang.query("(function_definition) @function_def")
        matches = query.matches(self.tree.root_node)
        functions = []

        for _pattern_index, captures_by_name in matches:
            function_def = captures_by_name["function_def"][0]

            # Extract function name based on definition type
            func_name = self._extract_cpp_function_name(function_def)

            if func_name is None:
                print("Could not parse function name for node:", function_def)
                func_name = "<unknown>"

            start_line, end_line = self.get_node_line_range(function_def)
            ts_node = function_def
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )
            functions.append(func)

        sorted_functions = sorted(functions, key=lambda x: x.start_byte)
        return sorted_functions

    def _extract_cpp_function_name(self, function_node: tree_sitter.Node) -> str | None:
        """Extract function name from C++ function definitions."""
        declarator_node = function_node.child_by_field_name("declarator")
        if not declarator_node:
            return None

        # Handle different declarator types
        if declarator_node.type == "function_declarator":
            # Regular function or method
            declarator = declarator_node.child_by_field_name("declarator")
            if declarator:
                if declarator.type == "identifier":
                    return declarator.text.decode("utf-8")
                elif declarator.type == "field_identifier":
                    # Method within class (e.g., inside class definition)
                    return declarator.text.decode("utf-8")
                elif declarator.type == "qualified_identifier":
                    # Extract the identifier part from qualified name (e.g., T::foo -> foo)
                    # Handle nested qualified identifiers like MyNamespace::Calculator::multiply
                    name_node = declarator.child_by_field_name("name")
                    if name_node:
                        if name_node.type == "identifier":
                            return name_node.text.decode("utf-8")
                        elif name_node.type == "qualified_identifier":
                            # Handle deeper nesting
                            inner_name = name_node.child_by_field_name("name")
                            if inner_name and inner_name.type == "identifier":
                                return inner_name.text.decode("utf-8")
                elif declarator.type == "destructor_name":
                    # Destructor like ~T
                    identifier = declarator.children[-1]  # Last child is the identifier
                    if identifier and identifier.type == "identifier":
                        return "~" + identifier.text.decode("utf-8")
                elif declarator.type == "operator_name":
                    # Operator overload like operator+
                    return (
                        "operator" + declarator.text.decode("utf-8")[8:]
                    )  # Remove "operator" prefix
                elif declarator.type == "operator_cast":
                    # Conversion operator
                    return "operator_cast"
        elif declarator_node.type == "qualified_identifier":
            # For cases like T::T() constructor
            name_node = declarator_node.child_by_field_name("name")
            if name_node and name_node.type == "identifier":
                return name_node.text.decode("utf-8")

        return None

    @symbol_extractor
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract class, struct, enum, union, and namespace definitions."""
        results = []

        # Define separate simple queries for different structure types
        queries = [
            ("(class_specifier) @definition", "class"),
            ("(struct_specifier) @definition", "struct"),
            ("(enum_specifier) @definition", "enum"),
            ("(union_specifier) @definition", "union"),
            ("(namespace_definition) @definition", "namespace"),
        ]

        for query_str, structure_type in queries:
            try:
                query = self.tree_sitter_lang.query(query_str)
                matches = query.matches(self.tree.root_node)

                for _pattern_idx, captures_dict in matches:
                    if "definition" in captures_dict:
                        data_structure_node = captures_dict["definition"][0]

                        # Extract name based on structure type
                        data_structure_name = self._extract_structure_name(
                            data_structure_node, structure_type
                        )

                        if data_structure_name:  # Only add if we found a name
                            start_line, end_line = self.get_node_line_range(
                                data_structure_node
                            )
                            ds = RawTreeSitterSymbolData(
                                name=data_structure_name,
                                start_line=start_line,
                                end_line=end_line,
                                symbol_kind=SymbolKind.DATA_STRUCTURE,
                                start_byte=data_structure_node.start_byte,
                                end_byte=data_structure_node.end_byte,
                                file_path=self.file_path,
                                symbol_code=node_to_text(data_structure_node),
                            )
                            results.append(ds)
            except Exception as e:
                print(f"Query error for {structure_type}: {e}")
                continue

        # Handle template classes separately
        try:
            template_query = self.tree_sitter_lang.query(
                "(template_declaration) @template_def"
            )
            template_matches = template_query.matches(self.tree.root_node)

            for _pattern_idx, captures_dict in template_matches:
                if "template_def" in captures_dict:
                    template_node = captures_dict["template_def"][0]

                    # Look for class_specifier within template
                    for child in template_node.children:
                        if child.type == "class_specifier":
                            class_name = self._extract_structure_name(child, "class")
                            if class_name:
                                start_line, end_line = self.get_node_line_range(
                                    template_node
                                )
                                ds = RawTreeSitterSymbolData(
                                    name=class_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                                    start_byte=template_node.start_byte,
                                    end_byte=template_node.end_byte,
                                    file_path=self.file_path,
                                    symbol_code=node_to_text(template_node),
                                )
                                results.append(ds)
                                break
        except Exception as e:
            print(f"Template query error: {e}")

        results.sort(key=lambda x: x.start_byte)
        return results

    def _extract_structure_name(
        self, node: tree_sitter.Node, structure_type: str
    ) -> str | None:
        """Extract name from structure definition node."""
        # For namespace, look for name field
        if structure_type == "namespace":
            name_node = node.child_by_field_name("name")
            if name_node and name_node.type == "identifier":
                return name_node.text.decode("utf-8")
        else:
            # For class/struct/enum/union, look for name field (should be type_identifier)
            name_node = node.child_by_field_name("name")
            if name_node and name_node.type == "type_identifier":
                return name_node.text.decode("utf-8")

        return None

    @symbol_extractor
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        """Extract global variable declarations."""
        query = self.tree_sitter_lang.query(
            """
            (declaration) @global_var
            """
        )
        matches = query.matches(self.tree.root_node)

        def is_top_level_or_namespace_or_preprocessor_wrapped(
            node: tree_sitter.Node,
        ) -> bool:
            """
            Returns True if the node is under translation_unit or namespace
            with only preprocessor nodes in between.
            """
            parent = node.parent
            while parent:
                if parent.type in ["translation_unit", "namespace_definition"]:
                    return True
                if not parent.type.startswith("preproc_"):
                    return False
                parent = parent.parent
            return False

        variables = []
        for _pattern_index, captures_by_name in matches:
            decl_node = captures_by_name["global_var"][0]

            if not is_top_level_or_namespace_or_preprocessor_wrapped(decl_node):
                continue

            start_line, end_line = self.get_node_line_range(decl_node)

            # Skip function declarations and definitions
            if any(
                child.type in ["function_declarator", "function_definition"]
                for child in decl_node.children
            ):
                continue

            # Skip type definitions
            if any(child.type == "type_definition" for child in decl_node.children):
                continue

            # Skip class, struct, enum definitions
            if any(
                child.type in ["class_specifier", "struct_specifier", "enum_specifier"]
                for child in decl_node.children
            ):
                continue

            # Find the identifier node(s) in this declaration
            for child in decl_node.children:
                if child.type in [
                    "identifier",
                    "init_declarator",
                    "pointer_declarator",
                    "array_declarator",
                    "reference_declarator",
                ]:
                    id_node = find_identifier_node(child)
                    if id_node:
                        var_name = id_node.text.decode("utf8")
                        ts_node = decl_node
                        var = RawTreeSitterSymbolData(
                            name=var_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.VARIABLE,
                            start_byte=ts_node.start_byte,
                            end_byte=ts_node.end_byte,
                            file_path=self.file_path,
                            symbol_code=node_to_text(ts_node),
                        )
                        variables.append(var)

        sorted_vars = sorted(variables, key=lambda x: x.start_byte)
        return sorted_vars

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        """Extract function calls including method calls and operator calls."""
        query = self.tree_sitter_lang.query(
            """
            [
              (call_expression) @call
              (field_expression
                argument: (identifier) @obj
                field: (field_identifier) @method_name
              ) @method_call
            ]
            """
        )
        matches = query.matches(self.tree.root_node)
        function_calls = []

        for _pattern_index, captures_by_name in matches:
            if "call" in captures_by_name:
                call_node = captures_by_name["call"][0]

                # Extract function name (identifier within call_expression)
                identifier_node = call_node.child_by_field_name("function")
                if identifier_node is None:
                    continue

                func_name = self._extract_call_name(identifier_node)
                if not func_name:
                    continue

                start_line, end_line = self.get_node_line_range(call_node)
                ts_node = call_node
                func_call = RawTreeSitterSymbolData(
                    name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.CALL,
                    start_byte=ts_node.start_byte,
                    end_byte=ts_node.end_byte,
                    file_path=self.file_path,
                    symbol_code=node_to_text(ts_node),
                )
                function_calls.append(func_call)

        # Sort the calls by their start byte
        sorted_calls = sorted(function_calls, key=lambda x: x.start_byte)
        return sorted_calls

    def _extract_call_name(self, identifier_node: tree_sitter.Node) -> str | None:
        """Extract function name from call expression, handling qualified names and member access."""
        if identifier_node.type == "identifier":
            return identifier_node.text.decode("utf-8")
        elif identifier_node.type == "field_expression":
            # Handle member function calls like obj.method()
            field_node = identifier_node.child_by_field_name("field")
            if field_node and field_node.type == "field_identifier":
                return field_node.text.decode("utf-8")
        elif identifier_node.type == "qualified_identifier":
            # Handle namespace qualified calls like std::cout
            name_node = identifier_node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode("utf-8")
        elif identifier_node.type == "scope_resolution":
            # Handle :: operator
            name_node = identifier_node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode("utf-8")

        return None

    @symbol_extractor
    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        """Extract all function declarations (not definitions) in the C++ code."""
        query = self.tree_sitter_lang.query(
            """
            [
              (declaration) @declaration
              (template_declaration
                (declaration) @template_declaration
              )
            ]
            """
        )
        matches = query.matches(self.tree.root_node)
        declarations = []

        for _pattern_index, captures_by_name in matches:
            if "declaration" in captures_by_name:
                declaration_node = captures_by_name["declaration"][0]
            elif "template_declaration" in captures_by_name:
                declaration_node = captures_by_name["template_declaration"][0]
            else:
                continue

            declarator_node = declaration_node.child_by_field_name("declarator")
            if not declarator_node:
                continue

            # Ensure it's a function declarator
            func_name, _ = get_function_name_and_params(declarator_node)
            if func_name is None:
                continue

            # Function declaration should not have a body
            has_body = any(
                child.type == "compound_statement"
                for child in declaration_node.children
            )
            if has_body:
                continue

            start_line, end_line = self.get_node_line_range(declaration_node)
            ts_node = declaration_node
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE_DECLARATION,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                symbol_code=node_to_text(ts_node),
            )
            declarations.append(func)

        sorted_declarations = sorted(declarations, key=lambda x: x.start_byte)
        return sorted_declarations


if __name__ == "__main__":
    """
    Test code; left with a known case our code does not fully handle yet so you can
    implement it!
    """

    # Test C code
    c_code = """typedef struct {
    int x;
    int y;
}
Point2, *Point2Ptr;
"""
    print("=== Testing C Driver Tree ===")
    c_driver_tree = CDriverTree.from_code(c_code, "test.c")
    c_data_structures = c_driver_tree.extract_data_structure_definitions()
    print("C Tree root children:", c_driver_tree.tree.root_node.children)
    print("C Data structures:", c_data_structures)

    # Test C++ code
    cpp_code = """#include <iostream>
#include <vector>

namespace MyNamespace {
    class Calculator {
    private:
        double value;

    public:
        Calculator(double initial_value) : value(initial_value) {}
        ~Calculator() {}

        double add(double x) {
            value += x;
            return value;
        }

        double multiply(double x);

        Calculator operator+(const Calculator& other) {
            return Calculator(value + other.value);
        }
    };

    template<typename T>
    class GenericContainer {
    public:
        T data;
        void set_data(T new_data) { data = new_data; }
    };
}

double MyNamespace::Calculator::multiply(double x) {
    value *= x;
    return value;
}

int main() {
    MyNamespace::Calculator calc(10.0);
    calc.add(5.0);
    std::cout << "Result: " << calc.multiply(2.0) << std::endl;
    return 0;
}
"""
    print("\n=== Testing C++ Driver Tree ===")
    cpp_driver_tree = CppDriverTree.from_code(cpp_code, "test.cpp")

    print("C++ Imports:")
    cpp_imports = cpp_driver_tree.extract_imports()
    for imp in cpp_imports:
        print(f"  {imp.name} at line {imp.start_line}")

    print("\nC++ Data Structures:")
    cpp_data_structures = cpp_driver_tree.extract_data_structure_definitions()
    for ds in cpp_data_structures:
        print(f"  {ds.name} at lines {ds.start_line}-{ds.end_line}")

    print("\nC++ Functions:")
    cpp_functions = cpp_driver_tree.extract_function_definitions()
    for func in cpp_functions:
        print(f"  {func.name} at lines {func.start_line}-{func.end_line}")

    print("\nC++ Function Calls:")
    cpp_calls = cpp_driver_tree.extract_function_calls()
    for call in cpp_calls:
        print(f"  {call.name} at line {call.start_line}")

    print("\nAll C++ Symbols:")
    all_symbols = cpp_driver_tree.extract_all_symbols()
    for symbol in all_symbols:
        print(f"  {symbol.symbol_kind.name}: {symbol.name} at line {symbol.start_line}")
