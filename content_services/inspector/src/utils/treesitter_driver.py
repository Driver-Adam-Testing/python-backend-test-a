from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from inspect import getmembers, ismethod
from pathlib import Path
from typing import Self

import tree_sitter
import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_python

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

LANGUAGES = {
    "c": tree_sitter.Language(tree_sitter_c.language()),
    "cpp": tree_sitter.Language(tree_sitter_cpp.language()),
    "python": tree_sitter.Language(tree_sitter_python.language()),
}

# TODO: First try to linkn methods to classes in symbol table construction
# TODO: nice to have: function calls attaching the scope so we can use in symbol table construction


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
    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
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


def get_function_name_and_params_and_scope_parts(
    declarator_node: tree_sitter.Node,
) -> tuple[str | None, tree_sitter.Node | None, list[str]]:
    """
    Extract the function name and parameter node from a function declarator.
    Handles attributes, nested declarators, qualified identifiers, and parenthesized declarators.
    """
    if declarator_node.type == "function_declarator":
        name_node = declarator_node.child_by_field_name("declarator")
        params_node = declarator_node.child_by_field_name("parameters")

        if name_node and name_node.type in ["identifier", "field_identifier"]:
            return name_node.text.decode("utf-8"), params_node, []
        elif name_node and name_node.type == "qualified_identifier":
            # Handle qualified names like ClassName::methodName or Namespace::Class::method
            func_name, scope_parts = (
                _extract_function_name_and_scope_from_qualified_identifier(name_node)
            )
            # scope = _extract_scope_from_qualified_identifier(name_node)
            return func_name, params_node, scope_parts
        elif name_node and name_node.type == "destructor_name":
            # Handle destructors like ~ClassName
            return name_node.text.decode("utf-8"), params_node, []
        elif name_node and name_node.type == "operator_name":
            # Handle operator overloads
            return name_node.text.decode("utf-8"), params_node, []
        elif name_node and name_node.type == "template_function":
            return name_node.text.decode("utf-8"), params_node, []
        elif name_node:
            # Recurse into nested declarators (e.g., parenthesized_declarator, pointer_declarator)
            return get_function_name_and_params_and_scope_parts(name_node)

    elif declarator_node.type in {
        "pointer_declarator",
        "parenthesized_declarator",
        "attributed_declarator",
    }:
        # Recurse into nested declarators
        inner_declarator = declarator_node.child_by_field_name("declarator")
        if inner_declarator:
            return get_function_name_and_params_and_scope_parts(inner_declarator)
    elif declarator_node.type == "reference_declarator":
        child_node = declarator_node.children[
            -1
        ]  # We get -1 child here, because children[0] appears to just be an & node
        if child_node.type == "function_declarator":
            # If it's a reference to a function, recurse into the function declarator
            return get_function_name_and_params_and_scope_parts(child_node)
        print(f"Unhandled reference_declarator child type: {child_node.type}")

    print(
        f"Unhandled declarator type: {declarator_node.type} in {declarator_node.text.decode('utf-8')}"
    )
    # Unsupported or unhandled declarator type
    return None, None, []


def _extract_function_name_and_scope_from_qualified_identifier(
    qualified_node: tree_sitter.Node,
) -> tuple[str | None, list[str]]:
    """
    Extract the function name from a qualified_identifier node.

    qualified_identifier has 'scope' and 'name' fields.
    The name field can be an identifier or another qualified_identifier.
    We want the final identifier as the function name.

    Examples:
    - MyClass::add -> "add"
    - MyClass::Inner::display -> "display"
    """
    scope_node = qualified_node.child_by_field_name("scope")
    scope_parts = [scope_node.text.decode("utf-8")]
    name_node = qualified_node.child_by_field_name("name")
    if not name_node:
        return None, []

    if name_node.type == "identifier" or name_node.type == "field_identifier":
        return name_node.text.decode("utf-8"), scope_parts
    elif name_node.type == "qualified_identifier":
        # Recursively extract from nested qualified identifier (e.g., MyClass::Inner::display)
        name, more_scope_parts = (
            _extract_function_name_and_scope_from_qualified_identifier(name_node)
        )
        return name, scope_parts + more_scope_parts
    elif name_node.type == "destructor_name":
        # Handle destructors like ~ClassName
        return name_node.text.decode("utf-8"), scope_parts
    elif name_node.type == "operator_name":
        # Handle operator overloads
        return name_node.text.decode("utf-8"), scope_parts

    print(
        f"Unhandled name node type: {name_node.type} in {qualified_node.text.decode('utf-8')}"
    )
    return None, []


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


@dataclass
class BaseClassInfo:
    name: str
    access_specifier: str | None = None  # "public", "private", "protected"
    is_virtual: bool = False

    def __str__(self) -> str:
        parts = []
        if self.is_virtual:
            parts.append("virtual")
        if self.access_specifier:
            parts.append(self.access_specifier)
        parts.append(self.name)
        return " ".join(parts)


def extract_base_class_info(base_class_clause: tree_sitter.Node) -> list[BaseClassInfo]:
    """
    Extract base class information from a base_class_clause node.

    Returns a list of BaseClassInfo objects containing:
    - name: The base class name (including templates and qualified names)
    - access_specifier: "public", "private", "protected", or None for default
    - is_virtual: True if virtual inheritance is used

    Handles:
    - Access specifiers (public, private, protected)
    - Virtual inheritance
    - Template base classes
    - Qualified names (namespace::Class)
    - Complex template expressions
    """
    if base_class_clause.type != "base_class_clause":
        return []

    base_classes = []

    # Look for base_class_specifier nodes within the base_class_clause
    for child in base_class_clause.children:
        if child.type == "base_class_specifier":
            base_class_info = _extract_single_base_class(child)
            if base_class_info:
                base_classes.append(base_class_info)
        elif child.type in [
            "type_identifier",
            "qualified_identifier",
            "template_type",
            "scoped_type_identifier",
            "dependent_type_identifier",
        ]:
            # Fallback for simpler cases where there's no base_class_specifier wrapper
            base_class_name = child.text.decode("utf8")
            if base_class_name:
                base_classes.append(BaseClassInfo(name=base_class_name))
        # Don't add anything else to avoid including access specifiers and punctuation
    return base_classes


def _extract_single_base_class(
    base_class_specifier: tree_sitter.Node,
) -> BaseClassInfo | None:
    """Extract information from a single base_class_specifier node."""
    name = None
    access_specifier = None
    is_virtual = False

    for child in base_class_specifier.children:
        if child.type == "virtual":
            is_virtual = True
        elif child.type in ["public", "private", "protected"]:
            access_specifier = child.type
        elif child.type in [
            "type_identifier",
            "qualified_identifier",
            "template_type",
            "template_argument_list",  # Handle template arguments
            "scoped_type_identifier",  # Handle scoped template types
            "dependent_type_identifier",  # Handle dependent template types
        ]:
            name = child.text.decode("utf8")
        elif name is None:
            # Fallback: if we haven't found a name yet and this child has text content,
            # it might be the base class name (handle unknown node types gracefully)
            child_text = child.text.decode("utf8").strip()
            if child_text and child_text not in [
                "virtual",
                "public",
                "private",
                "protected",
                ":",
                ",",
            ]:
                name = child_text

    if name:
        return BaseClassInfo(
            name=name, access_specifier=access_specifier, is_virtual=is_virtual
        )
    return None


class CppCDriverTree(DriverTree):
    language = "cpp"

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
            fully_qualified_path = self._get_fully_qualified_path_to_parent(
                include_directive_node
            )
            includes.append(
                RawTreeSitterSymbolData(
                    name=include_path_text,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.IMPORT,
                    start_byte=ts_node.start_byte,
                    end_byte=ts_node.end_byte,
                    file_path=self.file_path,
                    fully_qualified_parent_path=fully_qualified_path,
                    symbol_code=node_to_text(ts_node),
                    delimiter="::",
                )
            )
        sorted_includes = sorted(includes, key=lambda x: x.start_byte)

        return sorted_includes

    @symbol_extractor
    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        query = self.tree_sitter_lang.query("(function_definition) @function_def")
        matches = query.matches(self.tree.root_node)
        functions = []

        for _pattern_index, captures_by_name in matches:
            function_def = captures_by_name["function_def"][0]
            declarator_node = function_def.child_by_field_name("declarator")
            func_name, params_node, qualified_scope_parts = (
                get_function_name_and_params_and_scope_parts(declarator_node)
            )
            if func_name is None:
                print("Could not parse function name for node:", declarator_node)
                continue
            start_line, end_line = self.get_node_line_range(function_def)
            ts_node = function_def
            qualified_parent_path = self._get_fully_qualified_path_to_parent(
                function_def
            )
            fully_qualified_path = (
                qualified_parent_path
                + (
                    "::"
                    if len(qualified_scope_parts) > 0 and len(qualified_parent_path) > 0
                    else ""
                )
                + "::".join(qualified_scope_parts)
            )
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_path,
                symbol_code=node_to_text(ts_node),
                delimiter="::",
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

            (class_specifier
                name: (type_identifier) @class.name
                body: (field_declaration_list)? @class.body
            ) @class.definition
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
                case {"class.definition": [data_structure_node], **rest}:
                    if rest.get("class.body") is None:
                        # Skip classes without a body (forward declarations)
                        continue
                    name_nodes = rest.get("class.name", [])
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
                print("Could not parse name for node:", data_structure_node)
                continue  # No name found, skip this data structure

            start_line, end_line = self.get_node_line_range(data_structure_node)
            ts_node = data_structure_node
            fully_qualified_path = self._get_fully_qualified_path_to_parent(
                data_structure_node
            )
            base_class_info = None
            for child in data_structure_node.children:
                if (
                    child.type == "base_class_clause"
                ):  # TODO: add test cases for this extraction
                    base_class_info = extract_base_class_info(child)
                    break
            ds = RawTreeSitterSymbolData(
                name=data_structure_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.DATA_STRUCTURE,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_path,
                symbol_code=node_to_text(ts_node),
                delimiter="::",
                base_class_names=[bc.name for bc in base_class_info]
                if base_class_info
                else None,
            )

            results.append(ds)

        results.sort(key=lambda x: x.start_byte)
        return results

    def _get_fully_qualified_path_to_parent(self, node: tree_sitter.Node) -> str:
        """
        Extract the fully qualified path for a node, including namespaces and enclosing types.

        Traverses up the parent hierarchy to find enclosing scopes:
        - namespace_definition (including anonymous namespaces marked as "(anonymous)")
        - class_specifier (nested classes)
        - struct_specifier (nested in structs)
        - union_specifier (nested in unions)
        - enum_specifier (nested in enums)

        Returns the path with :: separators. Examples:
        - "MyNamespace::OuterClass::InnerClass" for named scopes
        - "(anonymous)::ClassName" for anonymous namespace
        - "Named::(anonymous)::ClassName" for mixed named/anonymous

        Note: this is the fully qualified path to the PARENT of the node, not the node itself.
        """
        path_parts = []
        current = node.parent

        while current:
            if current.type == "namespace_definition":
                name_node = current.child_by_field_name("name")
                if name_node and name_node.type in [
                    "identifier",
                    "namespace_identifier",
                ]:
                    path_parts.append(name_node.text.decode("utf-8"))
                elif not name_node:
                    # Anonymous namespace - add special marker
                    path_parts.append("(anonymous)")
            elif current.type in [
                "class_specifier",
                "struct_specifier",
                "union_specifier",
                "enum_specifier",
            ]:
                name_node = current.child_by_field_name("name")
                if name_node and name_node.type == "type_identifier":
                    path_parts.append(name_node.text.decode("utf-8"))
            elif current.type == "function_definition":
                declarator_node = current.child_by_field_name("declarator")
                if declarator_node:
                    # Function name is typically in the function_declarator
                    if declarator_node.type == "function_declarator":
                        name_node = declarator_node.child_by_field_name("declarator")
                        if name_node and name_node.type in [
                            "identifier",
                            "field_identifier",
                        ]:
                            path_parts.append(name_node.text.decode("utf-8"))
                    elif declarator_node.type in ["identifier", "field_identifier"]:
                        path_parts.append(declarator_node.text.decode("utf-8"))

            current = current.parent

        # Reverse to get the correct order (outermost to innermost)
        path_parts.reverse()
        return "::".join(path_parts) if path_parts else ""

    # @symbol_extractor
    # def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
    #     results = []

    #     query_str = """
    #         (class_specifier
    #             name: (type_identifier) @class.name
    #         ) @class.definition
    #     """

    #     try:
    #         query = self.tree_sitter_lang.query(query_str)
    #         matches = query.matches(self.tree.root_node)

    #         for _pattern_idx, captures_dict in matches:
    #             if "class.definition" in captures_dict:
    #                 class_node = captures_dict["class.definition"][0]
    #                 class_name_nodes = captures_dict["class.name"]
    #                 class_name = class_name_nodes[0].text.decode("utf8")

    #                 start_line, end_line = self.get_node_line_range(class_node)

    #                 # Build fully qualified path including namespaces and enclosing types
    #                 fully_qualified_path = self._get_fully_qualified_path_to_parent(
    #                     class_node
    #                 )

    #                 ds = RawTreeSitterSymbolData(
    #                     name=class_name,
    #                     start_line=start_line,
    #                     end_line=end_line,
    #                     symbol_kind=SymbolKind.DATA_STRUCTURE,
    #                     start_byte=class_node.start_byte,
    #                     end_byte=class_node.end_byte,
    #                     file_path=self.file_path,
    #                     fully_qualified_parent_path=fully_qualified_path,
    #                     symbol_code=node_to_text(class_node),
    #                     delimiter="::",
    #                 )
    #                 results.append(ds)

    #     except Exception as e:
    #         print(f"Query error for class: {e}")

    #     # # Handle template classes separately
    #     # try:
    #     #     template_query = self.tree_sitter_lang.query(
    #     #         "(template_declaration) @template_def"
    #     #     )
    #     #     template_matches = template_query.matches(self.tree.root_node)

    #     #     for _pattern_idx, captures_dict in template_matches:
    #     #         if "template_def" in captures_dict:
    #     #             template_node = captures_dict["template_def"][0]

    #     #             # Look for class_specifier within template
    #     #             for child in template_node.children:
    #     #                 if child.type == "class_specifier":
    #     #                     class_name = self._extract_structure_name(child, "class")
    #     #                     if class_name:
    #     #                         start_line, end_line = self.get_node_line_range(
    #     #                             template_node
    #     #                         )
    #     #                         ds = RawTreeSitterSymbolData(
    #     #                             name=class_name,
    #     #                             start_line=start_line,
    #     #                             end_line=end_line,
    #     #                             symbol_kind=SymbolKind.DATA_STRUCTURE,
    #     #                             start_byte=template_node.start_byte,
    #     #                             end_byte=template_node.end_byte,
    #     #                             file_path=self.file_path,
    #     #                             symbol_code=node_to_text(template_node),
    #     #                         )
    #     #                         results.append(ds)
    #     #                         break
    #     # except Exception as e:
    #     #     print(f"Template query error: {e}")

    #     results.sort(key=lambda x: x.start_byte)
    #     return results

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
                    "reference_declarator",
                ]:
                    id_node = find_identifier_node(child)
                    if id_node:
                        var_name = id_node.text.decode("utf8")
                        ts_node = decl_node
                        fully_qualified_path = self._get_fully_qualified_path_to_parent(
                            decl_node
                        )
                        var = RawTreeSitterSymbolData(
                            name=var_name,
                            start_line=start_line,
                            end_line=end_line,
                            symbol_kind=SymbolKind.VARIABLE,
                            start_byte=ts_node.start_byte,
                            end_byte=ts_node.end_byte,
                            file_path=self.file_path,
                            fully_qualified_parent_path=fully_qualified_path,
                            symbol_code=node_to_text(ts_node),
                            delimiter="::",
                        )
                        variables.append(var)

        sorted_vars = sorted(variables, key=lambda x: x.start_byte)
        return sorted_vars

    # TODO we really need to swap to byte position since we often have
    # multiple calls per line to disambiguate

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        query = self.tree_sitter_lang.query("""
                                            (call_expression
                                            function: (identifier) @call.name) @call
                                            """)
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
            fully_qualified_path = self._get_fully_qualified_path_to_parent(call_node)
            func_call = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALL,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_path,
                symbol_code=node_to_text(ts_node),
                delimiter="::",
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
        query_str = """
        (
            [
              ; Declaration variants
              ;; Normal declaration
              (declaration) @declaration
              ;; Field declaration
              (field_declaration) @declaration
            ]
        )
        """
        query = self.tree_sitter_lang.query(query_str)
        # query = self.tree_sitter_lang.query("(declaration) @declaration")
        matches = query.matches(self.tree.root_node)
        declarations = []

        for _pattern_index, captures_by_name in matches:
            declaration_node = captures_by_name["declaration"][0]

            declarator_node = declaration_node.child_by_field_name("declarator")
            if not declarator_node:
                continue

            # Ensure it's a function declarator implicitly by calling this and having it return something
            func_name, params_node, qualified_scope_parts = (
                get_function_name_and_params_and_scope_parts(declarator_node)
            )
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
            qualified_parent_path = self._get_fully_qualified_path_to_parent(
                declaration_node
            )
            fully_qualified_path = (
                qualified_parent_path
                + (
                    "::"
                    if len(qualified_scope_parts) > 0 and len(qualified_parent_path) > 0
                    else ""
                )
                + "::".join(qualified_scope_parts)
            )
            func = RawTreeSitterSymbolData(
                name=func_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE_DECLARATION,
                start_byte=ts_node.start_byte,
                end_byte=ts_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_path,
                symbol_code=node_to_text(ts_node),
                delimiter="::",
            )
            declarations.append(func)

        sorted_declarations = sorted(declarations, key=lambda x: x.start_byte)
        return sorted_declarations
