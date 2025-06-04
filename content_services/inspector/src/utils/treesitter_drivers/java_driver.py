from collections.abc import Callable

import tree_sitter

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

from .base import DriverTree, symbol_extractor


def java_node_to_text(node: tree_sitter.Node) -> str:
    return node.text.decode("utf8")


def is_class_method(node: tree_sitter.Node) -> bool:
    """Check if a method declaration is inside a class body."""
    parent = node.parent
    while parent:
        if (
            parent.type == "class_body"
            or parent.type == "enum_body"
            or parent.type == "interface_body"
        ):
            return True
        if parent.type in ["program"]:
            return False
        parent = parent.parent
    return False


def is_interface_method(node: tree_sitter.Node) -> bool:
    """Check if a method declaration is inside an interface body."""
    parent = node.parent
    while parent:
        if parent.type == "interface_body":
            return True
        if parent.type in ["class_body", "program"]:
            return False
        parent = parent.parent
    return False


def get_method_name_and_params(
    method_node: tree_sitter.Node,
) -> tuple[str | None, tree_sitter.Node | None]:
    """Extract method name and parameters from method declaration."""
    if (
        method_node.type == "method_declaration"
        or method_node.type == "constructor_declaration"
    ):
        name_node = method_node.child_by_field_name("name")
        params_node = method_node.child_by_field_name("parameters")

        if name_node and name_node.type == "identifier":
            return name_node.text.decode("utf-8"), params_node

    return None, None


class JavaDriverTree(DriverTree):
    language = "java"
    extensions = frozenset([".java"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        """
        Build the fully qualified path to the parent of the given node.
        Java uses dot notation for packages and nested classes.
        """
        path_parts = []
        current = node.parent

        # First, check if we have a package declaration at the root level
        package_name = None
        root_node = self.tree.root_node
        for child in root_node.children:
            if child.type == "package_declaration":
                # Look for scoped_identifier child
                for pkg_child in child.children:
                    if pkg_child.type == "scoped_identifier":
                        package_name = pkg_child.text.decode("utf-8")
                        break
                break

        while current:
            if current.type in [
                "class_declaration",
                "interface_declaration",
                "enum_declaration",
            ] or current.type in ["method_declaration", "constructor_declaration"]:
                name_node = current.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    path_parts.append(name_node.text.decode("utf-8"))
            current = current.parent

        path_parts.reverse()

        # Prepend package name if it exists
        if package_name:
            path_parts.insert(0, package_name)

        return sep.join(path_parts) if path_parts else ""

    def extract_all_symbols(self) -> list[RawTreeSitterSymbolData]:
        """Extract all symbols from the Java source code."""
        symbols = []
        symbols.extend(self.extract_imports())
        symbols.extend(self.extract_callable_definitions())
        symbols.extend(self.extract_data_structure_definitions())
        symbols.extend(self.extract_function_calls())
        symbols.extend(self.extract_variables())
        return sorted(symbols, key=lambda x: x.start_byte)

    @symbol_extractor
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        """Extract all import statements and package declarations from Java code."""
        import_query_str = """
        (import_declaration) @import_stmt
        (package_declaration) @package_stmt
        """.strip()

        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for _, captures_by_name in matches:
            if "import_stmt" in captures_by_name:
                import_node = captures_by_name["import_stmt"][0]

                # Extract the import path
                import_path = None
                for child in import_node.children:
                    if child.type == "scoped_identifier" or child.type == "identifier":
                        import_path = child.text.decode("utf-8")
                        break
                    elif child.type == "asterisk":
                        # Handle wildcard imports like java.util.*
                        prev_sibling = child.prev_sibling
                        if prev_sibling and prev_sibling.type == "scoped_identifier":
                            import_path = prev_sibling.text.decode("utf-8") + ".*"
                        break

                if import_path:
                    start_line, end_line = self.get_node_line_range(import_node)
                    fully_qualified_parent_path = (
                        self._get_fully_qualified_path_to_parent(import_node)
                    )

                    import_symbol = RawTreeSitterSymbolData(
                        name=import_path,
                        start_line=start_line,
                        end_line=end_line,
                        symbol_kind=SymbolKind.IMPORT,
                        start_byte=import_node.start_byte,
                        end_byte=import_node.end_byte,
                        file_path=self.file_path,
                        fully_qualified_parent_path=fully_qualified_parent_path,
                        symbol_code=java_node_to_text(import_node),
                        delimiter=".",
                    )
                    imports.append(import_symbol)

            elif "package_stmt" in captures_by_name:
                package_node = captures_by_name["package_stmt"][0]

                # Extract the package path
                package_path = None
                for child in package_node.children:
                    if child.type == "scoped_identifier" or child.type == "identifier":
                        package_path = child.text.decode("utf-8")
                        break

                if package_path:
                    start_line, end_line = self.get_node_line_range(package_node)
                    fully_qualified_parent_path = (
                        self._get_fully_qualified_path_to_parent(package_node)
                    )

                    package_symbol = RawTreeSitterSymbolData(
                        name=package_path,
                        start_line=start_line,
                        end_line=end_line,
                        symbol_kind=SymbolKind.IMPORT,  # Using IMPORT kind for package declarations
                        start_byte=package_node.start_byte,
                        end_byte=package_node.end_byte,
                        file_path=self.file_path,
                        fully_qualified_parent_path=fully_qualified_parent_path,
                        symbol_code=java_node_to_text(package_node),
                        delimiter=".",
                    )
                    imports.append(package_symbol)

        return sorted(imports, key=lambda x: x.start_byte)

    @symbol_extractor
    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract all method and constructor declarations."""
        methods = self.extract_method_definitions()
        constructors = self.extract_constructor_definitions()
        return methods + constructors

    # @symbol_extractor
    def extract_method_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract method declarations (excluding constructors)."""
        return self._extract_callable_definitions_by_type(
            "method_declaration", is_class_method
        )

    # @symbol_extractor
    def extract_constructor_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract constructor declarations."""
        return self._extract_callable_definitions_by_type(
            "constructor_declaration", is_class_method
        )

    def _extract_callable_definitions_by_type(
        self, node_type: str, filter_fn: Callable[[tree_sitter.Node], bool]
    ) -> list[RawTreeSitterSymbolData]:
        """Extract callable definitions of a specific type."""
        callable_query_str = f"""
        ({node_type}) @callable_def
        """.strip()

        query = self.tree_sitter_lang.query(callable_query_str)
        matches = query.matches(self.tree.root_node)
        callables = []

        for _pattern_index, captures_by_name in matches:
            callable_def_node = captures_by_name["callable_def"][0]

            if filter_fn and not filter_fn(callable_def_node):
                continue

            callable_name, _params_node = get_method_name_and_params(callable_def_node)
            if callable_name is None:
                print(f"Could not parse callable name for node: {callable_def_node}")
                continue

            start_line, end_line = self.get_node_line_range(callable_def_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                callable_def_node
            )

            callable_symbol = RawTreeSitterSymbolData(
                name=callable_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
                start_byte=callable_def_node.start_byte,
                end_byte=callable_def_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(callable_def_node),
                delimiter=".",
            )
            callables.append(callable_symbol)

        return sorted(callables, key=lambda x: x.start_byte)

    @symbol_extractor
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract class, interface, and enum declarations."""
        classes = self.extract_class_definitions()
        interfaces = self.extract_interface_definitions()
        enums = self.extract_enum_definitions()
        return classes + interfaces + enums

    # @symbol_extractor
    def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract class declarations."""
        class_query_str = """
        (class_declaration
          name: (identifier) @class_name) @class_def
        """.strip()

        query = self.tree_sitter_lang.query(class_query_str)
        matches = query.matches(self.tree.root_node)
        classes = []

        for _pattern_idx, captures_by_name in matches:
            class_node = captures_by_name["class_def"][0]
            class_name_node = captures_by_name["class_name"][0]

            if not class_name_node:
                print(f"Could not parse class name for node: {class_node}")
                continue

            class_name = class_name_node.text.decode("utf-8")
            start_line, end_line = self.get_node_line_range(class_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                class_node
            )

            # Extract superclass and interfaces information
            base_class_names = []

            # Look for superclass (extends clause)
            superclass_node = class_node.child_by_field_name("superclass")
            if superclass_node:
                for child in superclass_node.children:
                    if (
                        child.type == "type_identifier"
                        or child.type == "scoped_type_identifier"
                    ):
                        # Extract the superclass name
                        base_class_names.append(child.text.decode("utf-8"))

            # Look for interfaces (implements clause)
            interfaces_node = class_node.child_by_field_name("interfaces")
            if interfaces_node:
                # The interfaces field contains a super_interfaces node with type_list children
                for child in interfaces_node.children:
                    if child.type == "type_list":
                        for type_child in child.children:
                            if (
                                type_child.type == "type_identifier"
                                or type_child.type == "scoped_type_identifier"
                            ):
                                base_class_names.append(type_child.text.decode("utf-8"))

            class_symbol = RawTreeSitterSymbolData(
                name=class_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CLASS,
                start_byte=class_node.start_byte,
                end_byte=class_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(class_node),
                delimiter=".",
                base_class_names=base_class_names if base_class_names else None,
            )
            classes.append(class_symbol)

        return sorted(classes, key=lambda x: x.start_byte)

    # @symbol_extractor
    def extract_interface_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract interface declarations."""
        interface_query_str = """
        (interface_declaration
          name: (identifier) @interface_name) @interface_def
        """.strip()

        query = self.tree_sitter_lang.query(interface_query_str)
        matches = query.matches(self.tree.root_node)
        interfaces = []

        for _pattern_idx, captures_by_name in matches:
            interface_node = captures_by_name["interface_def"][0]
            interface_name_node = captures_by_name["interface_name"][0]

            if not interface_name_node:
                print(f"Could not parse interface name for node: {interface_node}")
                continue

            interface_name = interface_name_node.text.decode("utf-8")
            start_line, end_line = self.get_node_line_range(interface_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                interface_node
            )

            # Extract extended interfaces
            base_interface_names = []
            # Look for extends_interfaces child by type
            for child in interface_node.children:
                if child.type == "extends_interfaces":
                    # Look for type_list within extends_interfaces
                    for ext_child in child.children:
                        if ext_child.type == "type_list":
                            for type_child in ext_child.children:
                                if type_child.type == "type_identifier":
                                    base_interface_names.append(
                                        type_child.text.decode("utf-8")
                                    )
                    break

            interface_symbol = RawTreeSitterSymbolData(
                name=interface_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.INTERFACE,
                start_byte=interface_node.start_byte,
                end_byte=interface_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(interface_node),
                delimiter=".",
                base_class_names=base_interface_names if base_interface_names else None,
            )
            interfaces.append(interface_symbol)

        return sorted(interfaces, key=lambda x: x.start_byte)

    # @symbol_extractor
    def extract_enum_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract enum declarations."""
        enum_query_str = """
        (enum_declaration
          name: (identifier) @enum_name) @enum_def
        """.strip()

        query = self.tree_sitter_lang.query(enum_query_str)
        matches = query.matches(self.tree.root_node)
        enums = []

        for _pattern_idx, captures_by_name in matches:
            enum_node = captures_by_name["enum_def"][0]
            enum_name_node = captures_by_name["enum_name"][0]

            if not enum_name_node:
                print(f"Could not parse enum name for node: {enum_node}")
                continue

            enum_name = enum_name_node.text.decode("utf-8")
            start_line, end_line = self.get_node_line_range(enum_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                enum_node
            )

            enum_symbol = RawTreeSitterSymbolData(
                name=enum_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CLASS,
                start_byte=enum_node.start_byte,
                end_byte=enum_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(enum_node),
                delimiter=".",
            )
            enums.append(enum_symbol)

        return sorted(enums, key=lambda x: x.start_byte)

    @symbol_extractor
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        """Extract field declarations and local variables."""
        fields = self.extract_field_definitions()
        return fields

    # @symbol_extractor
    def extract_field_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract field declarations from classes and interfaces."""
        field_query_str = """
        (field_declaration
          declarator: (variable_declarator
            name: (identifier) @field_name)) @field_def
        """.strip()

        query = self.tree_sitter_lang.query(field_query_str)
        matches = query.matches(self.tree.root_node)
        fields = []

        for _pattern_idx, captures_by_name in matches:
            field_node = captures_by_name["field_def"][0]
            field_name_node = captures_by_name["field_name"][0]

            if not field_name_node:
                print(f"Could not parse field name for node: {field_node}")
                continue

            field_name = field_name_node.text.decode("utf-8")
            start_line, end_line = self.get_node_line_range(field_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                field_node
            )

            field_symbol = RawTreeSitterSymbolData(
                name=field_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.VARIABLE,
                start_byte=field_node.start_byte,
                end_byte=field_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(field_node),
                delimiter=".",
            )
            fields.append(field_symbol)

        return sorted(fields, key=lambda x: x.start_byte)

    @symbol_extractor
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        """Extract method invocations."""
        call_query_str = """
        (method_invocation
          name: (identifier) @call_name) @call_expr
        """.strip()

        query = self.tree_sitter_lang.query(call_query_str)
        matches = query.matches(self.tree.root_node)
        function_calls = []

        for _pattern_idx, captures_by_name in matches:
            call_node = captures_by_name["call_expr"][0]
            call_name_node = captures_by_name["call_name"][0]

            if not call_name_node:
                continue

            call_name = call_name_node.text.decode("utf-8")
            start_line, end_line = self.get_node_line_range(call_node)
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                call_node
            )

            call_symbol = RawTreeSitterSymbolData(
                name=call_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALL,
                start_byte=call_node.start_byte,
                end_byte=call_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=java_node_to_text(call_node),
                delimiter=".",
            )
            function_calls.append(call_symbol)

        return sorted(function_calls, key=lambda x: x.start_byte)
