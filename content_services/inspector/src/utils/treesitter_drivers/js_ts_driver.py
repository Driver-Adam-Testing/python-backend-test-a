"""
TypeScript tree-sitter driver implementation
"""

from dataclasses import dataclass
from typing import ClassVar

from tree_sitter import Node

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

from .base import DriverTree

# TODO: Currently does not support .tsx and .jsx files


@dataclass
class JsTsDriverTree(DriverTree):
    """Tree-sitter driver for TypeScript language"""

    language: ClassVar[str] = "js_ts"
    extensions: ClassVar[set[str]] = {
        ".ts",
        ".js",
    }  # TODO: extensions is likely not needed anymore

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        """Extract import statements from TypeScript code"""
        imports = []

        # Query for different import types
        import_query = self.tree_sitter_lang.query("""
            (import_statement) @import
            (import_clause) @clause
            (namespace_import) @namespace
            (named_imports) @named
            (import_specifier) @specifier
            (import_require_clause) @require
        """)

        captures_dict = import_query.captures(self.tree.root_node)

        # Process import statements
        if "import" in captures_dict:
            for node in captures_dict["import"]:
                # Handle full import statement
                import_text = self._get_node_text(node)
                imports.append(
                    self._create_symbol_data(
                        node=node,
                        name=import_text,
                        kind=SymbolKind.IMPORT,
                        parent_path="",
                    )
                )

        # Also handle require() style imports
        require_query = self.tree_sitter_lang.query("""
            (variable_declarator
              name: (identifier) @name
              value: (call_expression
                function: (identifier) @func (#eq? @func "require")
                arguments: (arguments (string) @module)
              )
            ) @declarator
        """)

        require_captures = require_query.captures(self.tree.root_node)
        if "declarator" in require_captures:
            for node in require_captures["declarator"]:
                name_node = node.child_by_field_name("name")
                if name_node:
                    imports.append(
                        self._create_symbol_data(
                            node=node,
                            name=self._get_node_text(name_node),
                            kind=SymbolKind.IMPORT,
                            parent_path="",
                        )
                    )

        # Handle dynamic imports (import() expressions)
        dynamic_import_query = self.tree_sitter_lang.query("""
            (call_expression
              function: (import) @import_keyword
            ) @dynamic_import
        """)

        dynamic_captures = dynamic_import_query.captures(self.tree.root_node)
        if "dynamic_import" in dynamic_captures:
            for node in dynamic_captures["dynamic_import"]:
                # Check if this is part of a variable declaration or await expression
                parent = node.parent
                while parent and parent.type in [
                    "await_expression",
                    "parenthesized_expression",
                ]:
                    parent = parent.parent

                # Get the full import expression
                import_text = self._get_node_text(node)
                imports.append(
                    self._create_symbol_data(
                        node=node,
                        name=import_text,
                        kind=SymbolKind.IMPORT,
                        parent_path="",
                    )
                )

        # Handle import.meta access
        import_meta_query = self.tree_sitter_lang.query("""
            (member_expression
              object: (meta_property) @meta
            ) @import_meta
        """)

        meta_captures = import_meta_query.captures(self.tree.root_node)
        if "import_meta" in meta_captures:
            for node in meta_captures["import_meta"]:
                # Get the full import.meta expression
                meta_text = self._get_node_text(node)
                imports.append(
                    self._create_symbol_data(
                        node=node,
                        name=meta_text,
                        kind=SymbolKind.IMPORT,
                        parent_path="",
                    )
                )

        return sorted(imports, key=lambda x: x.start_byte)

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract function and method definitions"""
        callables = []

        # Query for functions
        function_query = self.tree_sitter_lang.query("""
            (function_declaration
              name: (identifier) @name
            ) @function

            (generator_function_declaration
              name: (identifier) @name
            ) @generator

            (generator_function
              name: (identifier)? @name
            ) @generator

            (variable_declarator
              name: (identifier) @var_name
              value: [(arrow_function) (function_expression) (generator_function)] @func_value
            ) @var_func
        """)

        processed_nodes = set()

        function_captures = function_query.captures(self.tree.root_node)

        # Process function declarations
        if "function" in function_captures:
            for node in function_captures["function"]:
                # if node in processed_nodes:
                #     continue
                name_node = self._find_child_by_type(node, "identifier")
                if name_node:
                    processed_nodes.add(node)
                    callables.append(
                        self._create_symbol_data(
                            node=node,
                            name=self._get_node_text(name_node),
                            kind=SymbolKind.CALLABLE,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        # Process methods
        method_query = self.tree_sitter_lang.query("""
            (method_definition
              name: [(property_identifier) @method_name
                     (private_property_identifier) @private_method_name
                     (computed_property_name) @computed_name]
            ) @method

            (method_definition
              (computed_property_name
                [(template_string) @template_computed
                 (member_expression) @member_computed
                 (binary_expression) @binary_computed]
              )
            ) @computed_method
        """)

        method_captures = method_query.captures(self.tree.root_node)

        if "method" in method_captures:
            for node in method_captures["method"]:
                if node in processed_nodes:
                    continue

                name_node = self._find_child_by_field(node, "name")
                if name_node:
                    processed_nodes.add(node)

                    # Handle different name types
                    if name_node.type == "computed_property_name":
                        # Extract the content of computed property
                        name_text = self._get_node_text(name_node)
                    else:
                        name_text = self._get_node_text(name_node)

                    callables.append(
                        self._create_symbol_data(
                            node=node,
                            name=name_text,
                            kind=SymbolKind.CALLABLE,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        # Process generator functions
        if "generator" in function_captures:
            for node in function_captures["generator"]:
                name_node = self._find_child_by_field(node, "name")
                if name_node:
                    processed_nodes.add(node)
                    callables.append(
                        self._create_symbol_data(
                            node=node,
                            name=self._get_node_text(name_node),
                            kind=SymbolKind.CALLABLE,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        # Process arrow functions (including anonymous ones)
        if "arrow" in function_captures:
            for node in function_captures["arrow"]:
                processed_nodes.add(node)
                # Arrow functions might be anonymous
                callables.append(
                    self._create_symbol_data(
                        node=node,
                        name=None,  # Anonymous function
                        kind=SymbolKind.CALLABLE,
                        parent_path=self._get_fully_qualified_path_to_parent(node),
                    )
                )

        # Process variable functions
        if "var_func" in function_captures:
            for node in function_captures["var_func"]:
                # Variable assigned to function
                value_node = self._find_child_by_field(node, "value")
                if value_node.type == "function_expression":
                    name_node = self._find_child_by_field(value_node, "name")
                    if name_node is None:
                        name_node = self._find_child_by_field(node, "name")
                else:
                    name_node = self._find_child_by_field(node, "name")
                if name_node:
                    processed_nodes.add(node)
                    callables.append(
                        self._create_symbol_data(
                            node=node,
                            name=self._get_node_text(name_node),
                            kind=SymbolKind.CALLABLE,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        return sorted(callables, key=lambda x: x.start_byte)

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract classes, interfaces, enums, and type aliases"""
        # TODO: Handle objects with methods that aren't classes
        # e.g.
        # const obj = {
        #   method() {}
        # }
        structures = []

        # Query for different structure types
        structure_query = self.tree_sitter_lang.query("""
            (class_declaration
              name: (type_identifier) @name
            ) @class

            (interface_declaration
              name: (type_identifier) @name
            ) @interface

            (enum_declaration
              name: (identifier) @name
            ) @enum

            (type_alias_declaration
              name: (type_identifier) @name
              value: (object_type) @value
            ) @type_alias

            (abstract_class_declaration
              name: (type_identifier) @name
            ) @abstract_class

            (variable_declarator
              name: (identifier) @var_name
              value: (class) @class_expr
            ) @class_var
        """)

        processed_nodes = set()

        structure_captures = structure_query.captures(self.tree.root_node)

        # Process each type of structure
        for capture_type, nodes in structure_captures.items():
            for node in nodes:
                if node in processed_nodes:
                    continue

                # Handle class expressions differently
                if capture_type == "class_var":
                    # For variable declarator with class expression
                    name_node = self._find_child_by_field(node, "name")
                    value_node = self._find_child_by_field(node, "value")
                    if value_node:
                        processed_nodes.add(node)
                        # Check if the class expression has its own name
                        class_name = None
                        if value_node.type == "class":
                            # Check if the class has a name
                            class_name_node = value_node.child_by_field_name("name")
                            if class_name_node:
                                class_name = self._get_node_text(class_name_node)

                        # Use the class expression node for location
                        structures.append(
                            self._create_symbol_data(
                                node=value_node,
                                name=class_name,  # None for anonymous classes
                                kind=SymbolKind.CLASS,
                                parent_path=self._get_fully_qualified_path_to_parent(
                                    node
                                ),
                            )
                        )
                elif capture_type == "interface":
                    name_node = self._find_child_by_field(node, "name")
                    if name_node:
                        kind = SymbolKind.INTERFACE
                        parent_path = self._get_fully_qualified_path_to_parent(node)
                        base_interfaces = []
                        for child in node.children:
                            if child.type == "extends_type_clause":
                                # Check for base interfaces
                                base_interfaces = []
                                for base in child.children:
                                    if base.type == "type_identifier":
                                        base_interfaces.append(
                                            self._get_node_text(base)
                                        )
                        structures.append(
                            self._create_symbol_data(
                                node=node,
                                name=self._get_node_text(name_node),
                                kind=kind,
                                parent_path=parent_path,
                                base_class_names=(
                                    base_interfaces if base_interfaces else None
                                ),
                            )
                        )
                else:
                    # Handle regular class/interface/enum declarations
                    name_node = self._find_child_by_field(node, "name")
                    if name_node:
                        processed_nodes.add(node)
                        base_classes_and_interfaces = []
                        for child in node.children:
                            if child.type == "class_heritage":
                                for base in child.children:
                                    if base.type == "extends_clause":
                                        base_class_name_node = (
                                            self._find_child_by_field(base, "value")
                                        )
                                        base_classes_and_interfaces.append(
                                            self._get_node_text(base_class_name_node)
                                        )
                                    elif base.type == "implements_clause":
                                        for iface in base.children:
                                            if iface.type == "type_identifier":
                                                base_classes_and_interfaces.append(
                                                    self._get_node_text(iface)
                                                )

                        # Determine kind based on capture type
                        if capture_type in ["class", "abstract_class"]:
                            kind = SymbolKind.CLASS
                        elif capture_type == "enum":
                            kind = (
                                SymbolKind.DATA_STRUCTURE
                            )  # Use DATA_STRUCTURE for enum
                        elif capture_type == "type_alias":
                            kind = (
                                SymbolKind.DATA_STRUCTURE
                            )  # Use DATA_STRUCTURE for type alias
                        else:
                            kind = SymbolKind.DATA_STRUCTURE

                        parent_path = self._get_fully_qualified_path_to_parent(node)
                        structures.append(
                            self._create_symbol_data(
                                node=node,
                                name=self._get_node_text(name_node),
                                kind=kind,
                                parent_path=parent_path,
                                base_class_names=(
                                    base_classes_and_interfaces
                                    if base_classes_and_interfaces
                                    else None
                                ),
                            )
                        )

        sorted_structures = sorted(structures, key=lambda x: x.start_byte)
        return sorted_structures

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        """Extract function and method calls"""
        calls = []

        call_query = self.tree_sitter_lang.query("""
            (call_expression
              function: [(identifier) @func_name
                        (non_null_expression) @nonnull]
            ) @call
        """)

        processed_nodes = set()

        call_captures = call_query.captures(self.tree.root_node)

        # Process call expressions
        if "call" in call_captures:
            for node in call_captures["call"]:
                if node in processed_nodes:
                    continue
                function_node = self._find_child_by_field(node, "function")
                if function_node:
                    processed_nodes.add(node)

                    # Determine call type and name
                    if function_node.type == "member_expression":
                        # Method call like obj.method()
                        property_node = self._find_child_by_field(
                            function_node, "property"
                        )
                        if property_node:
                            name = self._get_node_text(property_node)
                        else:
                            name = self._get_node_text(function_node)
                    else:
                        # Simple function call
                        name = self._get_node_text(function_node)

                    calls.append(
                        self._create_symbol_data(
                            node=node,
                            name=name,
                            kind=SymbolKind.CALL,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        # Process new expressions
        if "new" in call_captures:
            for node in call_captures["new"]:
                if node in processed_nodes:
                    continue
                # Constructor call
                constructor_node = self._find_child_by_field(node, "constructor")
                if constructor_node:
                    processed_nodes.add(node)
                    name = self._get_node_text(constructor_node)
                    calls.append(
                        self._create_symbol_data(
                            node=node,
                            name=f"new {name}",
                            kind=SymbolKind.CALL,
                            parent_path=self._get_fully_qualified_path_to_parent(node),
                        )
                    )

        return sorted(calls, key=lambda x: x.start_byte)

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        """Extract variable declarations"""
        variables = []

        variable_query = self.tree_sitter_lang.query("""
            (program
                (_
                (variable_declarator
                name: (identifier) @var_name
                value: (_) @var_value
                ) @declarator))

            (program
                (export_statement
                (_
                (variable_declarator
                name: (identifier) @var_name
                value: (_) @var_value
                ) @declarator)))
        """)

        processed_nodes = set()

        variable_captures = variable_query.captures(self.tree.root_node)

        # Process variable declarators
        if "declarator" in variable_captures:
            for node in variable_captures["declarator"]:
                if node not in processed_nodes:
                    name_node = self._find_child_by_field(node, "name")
                    value_node = self._find_child_by_field(node, "value")
                    if value_node.type in [
                        "class",
                        "arrow_function",
                        "function_expression",
                        "generator_function",
                        "call_expression",
                    ]:
                        # Skip other handled variable_declarator cases
                        continue
                    if name_node:
                        processed_nodes.add(node)

                        if name_node.type == "identifier":
                            # Simple variable
                            variables.append(
                                self._create_symbol_data(
                                    node=node,
                                    name=self._get_node_text(name_node),
                                    kind=SymbolKind.VARIABLE,
                                    parent_path=self._get_fully_qualified_path_to_parent(
                                        node
                                    ),
                                )
                            )
        sorted_vars = sorted(variables, key=lambda x: x.start_byte)
        return sorted_vars

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def _get_fully_qualified_path_to_parent(self, node: Node) -> str:
        """Build fully qualified path to parent symbol"""
        path_parts = []
        current = node.parent

        while current:
            # Check if current node is a named container
            if (
                current.type == "class_declaration"
                or current.type == "abstract_class_declaration"
                or current.type == "interface_declaration"
                or current.type in ["internal_module", "module"]
                or current.type == "enum_declaration"
            ):
                name_node = self._find_child_by_field(current, "name")
                if name_node:
                    path_parts.append(self._get_node_text(name_node))

            elif current.type == "object_literal" or current.type == "object":
                # For object literals, try to find the variable/property name
                parent = current.parent
                if (
                    parent
                    and parent.type == "variable_declarator"
                    or parent
                    and parent.type == "property_assignment"
                ):
                    name_node = self._find_child_by_field(parent, "name")
                    if name_node:
                        path_parts.append(self._get_node_text(name_node))
            elif current.type == "program":
                path_parts.append(str(self.file_path.with_suffix("")))

            current = current.parent

        path_parts.reverse()
        return ".".join(path_parts)

    def _find_child_by_type(self, node: Node, child_type: str) -> Node | None:
        """Find first child node of given type"""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _find_child_by_field(self, node: Node, field_name: str) -> Node | None:
        """Find child node by field name"""
        return node.child_by_field_name(field_name)

    def _get_node_text(self, node: Node) -> str:
        """Get the text content of a node"""
        return self.source_bytes[node.start_byte : node.end_byte].decode("utf-8")

    def _create_symbol_data(
        self,
        node: Node,
        name: str,
        kind: SymbolKind,
        parent_path: str,
        base_class_names: list[str] | None = None,
    ) -> RawTreeSitterSymbolData:
        """Create a RawTreeSitterSymbolData from a node"""
        start_line, end_line = self.get_node_line_range(node)
        return RawTreeSitterSymbolData(
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            symbol_kind=kind,
            fully_qualified_parent_path=parent_path,
            file_path=self.file_path,
            symbol_code=self._get_node_text(node),
            delimiter=".",
            base_class_names=base_class_names,
        )
