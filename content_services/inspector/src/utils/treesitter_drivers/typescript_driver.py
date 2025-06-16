"""
TypeScript tree-sitter driver implementation
"""

from dataclasses import dataclass
from typing import ClassVar

from tree_sitter import Node

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

from .base import DriverTree


@dataclass
class TypeScriptDriverTree(DriverTree):
    """Tree-sitter driver for TypeScript language"""

    language: ClassVar[str] = "typescript"
    extensions: ClassVar[set[str]] = {".ts", ".tsx", ".mts", ".cts"}

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

        return imports

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract function and method definitions"""
        callables = []

        # Query for functions
        function_query = self.tree_sitter_lang.query("""
            (function_declaration
              name: (identifier) @name
            ) @function

            (function_expression
              name: (identifier)? @name
            ) @function

            (arrow_function) @arrow

            (generator_function_declaration
              name: (identifier) @name
            ) @generator

            (method_definition
              name: (property_identifier) @name
            ) @method

            (method_signature
              name: (property_identifier) @name
            ) @method_sig

            (variable_declarator
              name: (identifier) @var_name
              value: [(arrow_function) (function_expression)] @func_value
            ) @var_func
        """)

        processed_nodes = set()

        function_captures = function_query.captures(self.tree.root_node)

        # Process function declarations
        if "function" in function_captures:
            for node in function_captures["function"]:
                if node in processed_nodes:
                    continue
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
        if "method" in function_captures:
            for node in function_captures["method"]:
                if node in processed_nodes:
                    continue
                name_node = self._find_child_by_field(node, "name")
                if name_node:
                    processed_nodes.add(node)
                    parent_path = self._get_fully_qualified_path_to_parent(node)
                    callables.append(
                        self._create_symbol_data(
                            node=node,
                            name=self._get_node_text(name_node),
                            kind=SymbolKind.CALLABLE,
                            parent_path=parent_path,
                        )
                    )

        # Process variable functions
        if "var_func" in function_captures:
            for node in function_captures["var_func"]:
                if node in processed_nodes:
                    continue
                # Variable assigned to function
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

        # Extract getters and setters
        accessor_query = self.tree_sitter_lang.query("""
            (getter
              name: (property_identifier) @name
            ) @getter

            (setter
              name: (property_identifier) @name
            ) @setter
        """)

        accessor_captures = accessor_query.captures(self.tree.root_node)

        # Process getters
        if "getter" in accessor_captures:
            for node in accessor_captures["getter"]:
                if node not in processed_nodes:
                    name_node = self._find_child_by_field(node, "name")
                    if name_node:
                        processed_nodes.add(node)
                        parent_path = self._get_fully_qualified_path_to_parent(node)
                        callables.append(
                            self._create_symbol_data(
                                node=node,
                                name=self._get_node_text(name_node),
                                kind=SymbolKind.CALLABLE,
                                parent_path=parent_path,
                            )
                        )

        # Process setters
        if "setter" in accessor_captures:
            for node in accessor_captures["setter"]:
                if node not in processed_nodes:
                    name_node = self._find_child_by_field(node, "name")
                    if name_node:
                        processed_nodes.add(node)
                        parent_path = self._get_fully_qualified_path_to_parent(node)
                        callables.append(
                            self._create_symbol_data(
                                node=node,
                                name=self._get_node_text(name_node),
                                kind=SymbolKind.CALLABLE,
                                parent_path=parent_path,
                            )
                        )

        return callables

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract classes, interfaces, enums, and type aliases"""
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
                elif capture_type == "var_name":
                    # Skip var_name captures, they're handled with class_var
                    continue
                elif capture_type == "class_expr":
                    # Skip class_expr captures, they're handled with class_var
                    continue
                else:
                    # Handle regular class/interface/enum declarations
                    name_node = self._find_child_by_field(node, "name")
                    if name_node:
                        processed_nodes.add(node)

                        # Determine kind based on capture type
                        if capture_type in ["class", "abstract_class"]:
                            kind = SymbolKind.CLASS
                        elif capture_type == "interface":
                            kind = SymbolKind.INTERFACE
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
                            )
                        )

        # Also handle namespace/module declarations
        namespace_query = self.tree_sitter_lang.query("""
            (internal_module
              name: (identifier) @name
            ) @namespace

            (module
              name: (string) @name
            ) @module
        """)

        namespace_captures = namespace_query.captures(self.tree.root_node)

        # Process namespaces and modules
        for capture_type, nodes in namespace_captures.items():
            if capture_type in ["namespace", "module"]:
                for node in nodes:
                    if node not in processed_nodes:
                        name_node = self._find_child_by_field(node, "name")
                        if name_node:
                            processed_nodes.add(node)
                            structures.append(
                                self._create_symbol_data(
                                    node=node,
                                    name=self._get_node_text(name_node),
                                    kind=SymbolKind.MODULE,  # Use MODULE for namespaces
                                    parent_path=self._get_fully_qualified_path_to_parent(
                                        node
                                    ),
                                )
                            )

        return structures

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        """Extract function and method calls"""
        calls = []

        call_query = self.tree_sitter_lang.query("""
            (call_expression
              function: [(identifier) @func_name
                        (member_expression) @member_expr
                        (subscript_expression) @subscript]
            ) @call

            (new_expression
              constructor: [(identifier) @constructor_name
                           (member_expression) @constructor_member]
            ) @new
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

        return calls

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        """Extract variable declarations"""
        variables = []

        variable_query = self.tree_sitter_lang.query("""
            (variable_declarator
              name: [(identifier) @var_name
                    (object_pattern) @destructure_obj
                    (array_pattern) @destructure_arr]
            ) @declarator

            (const_declaration) @const_decl
            (let_declaration) @let_decl
            (var_declaration) @var_decl
        """)

        processed_nodes = set()

        variable_captures = variable_query.captures(self.tree.root_node)

        # Process variable declarators
        if "declarator" in variable_captures:
            for node in variable_captures["declarator"]:
                if node not in processed_nodes:
                    name_node = self._find_child_by_field(node, "name")
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
                        elif name_node.type in ["object_pattern", "array_pattern"]:
                            # Destructuring - extract individual identifiers
                            self._extract_destructured_variables(
                                name_node, node, variables
                            )

        # Also handle parameter properties in constructors
        param_prop_query = self.tree_sitter_lang.query("""
            (parameter
              decorator: [(public) (private) (protected) (readonly)] @modifier
              name: (identifier) @param_name
            ) @param
        """)

        param_captures = param_prop_query.captures(self.tree.root_node)

        # Process parameter properties
        if "param" in param_captures:
            for node in param_captures["param"]:
                if node not in processed_nodes:
                    # Check if this is in a constructor
                    parent = node.parent
                    while parent and parent.type != "constructor":
                        parent = parent.parent

                    if parent and parent.type == "constructor":
                        name_node = self._find_child_by_field(node, "name")
                        if name_node:
                            processed_nodes.add(node)
                            class_node = self._find_parent_class(parent)
                            parent_path = (
                                self._get_fully_qualified_path_to_parent(class_node)
                                if class_node
                                else ""
                            )

                            variables.append(
                                self._create_symbol_data(
                                    node=node,
                                    name=self._get_node_text(name_node),
                                    kind=SymbolKind.VARIABLE,
                                    parent_path=parent_path,
                                )
                            )

        return variables

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        """Extract function declarations (signatures without implementation)"""
        declarations = []

        # In TypeScript, function declarations are typically in:
        # 1. Interface method signatures
        # 2. Abstract method declarations
        # 3. Overload signatures
        # 4. Declare function statements

        declaration_query = self.tree_sitter_lang.query("""
            (method_signature
              name: (property_identifier) @name
            ) @method_sig

            (abstract_method_signature
              name: (property_identifier) @name
            ) @abstract_sig

            (function_signature
              name: (identifier) @name
            ) @func_sig

            (ambient_declaration
              (function_declaration
                name: (identifier) @name
              )
            ) @ambient_func
        """)

        processed_nodes = set()

        declaration_captures = declaration_query.captures(self.tree.root_node)

        # Process each type of declaration
        for capture_type, nodes in declaration_captures.items():
            for node in nodes:
                if node not in processed_nodes:
                    name_node = None

                    if capture_type in ["method_sig", "abstract_sig"]:
                        name_node = self._find_child_by_field(node, "name")
                    elif capture_type == "func_sig":
                        name_node = self._find_child_by_type(node, "identifier")
                    elif capture_type == "ambient_func":
                        # Find the function declaration inside
                        func_decl = self._find_child_by_type(
                            node, "function_declaration"
                        )
                        if func_decl:
                            name_node = self._find_child_by_field(func_decl, "name")
                            node = func_decl

                    if name_node:
                        processed_nodes.add(node)
                        declarations.append(
                            self._create_symbol_data(
                                node=node,
                                name=self._get_node_text(name_node),
                                kind=SymbolKind.CALLABLE_DECLARATION,
                                parent_path=self._get_fully_qualified_path_to_parent(
                                    node
                                ),
                            )
                        )

        return declarations

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

            current = current.parent

        path_parts.reverse()
        return ".".join(path_parts)

    def _extract_destructured_variables(
        self,
        pattern_node: Node,
        declarator_node: Node,
        variables: list[RawTreeSitterSymbolData],
    ) -> None:
        """Extract individual variables from destructuring patterns"""
        if pattern_node.type == "identifier":
            variables.append(
                self._create_symbol_data(
                    node=declarator_node,
                    name=self._get_node_text(pattern_node),
                    kind=SymbolKind.VARIABLE,
                    parent_path=self._get_fully_qualified_path_to_parent(
                        declarator_node
                    ),
                )
            )
        elif pattern_node.type == "object_pattern":
            # Extract each property
            for child in pattern_node.children:
                if child.type == "shorthand_property_identifier":
                    variables.append(
                        self._create_symbol_data(
                            node=declarator_node,
                            name=self._get_node_text(child),
                            kind=SymbolKind.VARIABLE,
                            parent_path=self._get_fully_qualified_path_to_parent(
                                declarator_node
                            ),
                        )
                    )
                elif child.type == "pair_pattern":
                    value_node = self._find_child_by_field(child, "value")
                    if value_node:
                        self._extract_destructured_variables(
                            value_node, declarator_node, variables
                        )
        elif pattern_node.type == "array_pattern":
            # Extract each element
            for child in pattern_node.children:
                if child.type != "," and child.type != "[" and child.type != "]":
                    self._extract_destructured_variables(
                        child, declarator_node, variables
                    )

    def _find_parent_class(self, node: Node) -> Node | None:
        """Find the parent class declaration"""
        current = node
        while current:
            if current.type in ["class_declaration", "abstract_class_declaration"]:
                return current
            current = current.parent
        return None

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
        self, node: Node, name: str, kind: SymbolKind, parent_path: str
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
        )
