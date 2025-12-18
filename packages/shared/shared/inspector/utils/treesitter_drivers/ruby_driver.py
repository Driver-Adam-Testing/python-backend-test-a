from dataclasses import dataclass
from enum import StrEnum

import tree_sitter
from pydantic import ConfigDict
from shared.inspector.utils.lang_specialization.symbol_common import (
    BespokeMarker,
    RawTreeSitterSymbolData,
    SymbolKind,
)
from shared.inspector.utils.treesitter_drivers.base import DriverTree


class RubyVariableKind(StrEnum):
    VARIABLE = "variable"
    CONSTANT = "constant"
    ATTRIBUTE = "attribute"


class RubyVisibilityKind(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


class RubyAttributeAccessKind(StrEnum):
    READ = "R"
    WRITE = "W"
    READ_WRITE = "RW"


class RubyMethodKind(StrEnum):
    INSTANCE_METHOD = "Instance Method"
    CLASS_METHOD = "Class Method"
    MODULE_METHOD = "Module Method"
    TOP_LEVEL = "Top Level Method"


class RubyRequireBespokeMarker(BespokeMarker):
    is_relative: bool
    model_config = ConfigDict(frozen=True)


class RubyVariableBespokeMarker(BespokeMarker):
    kind: RubyVariableKind
    access: RubyAttributeAccessKind | None
    is_top_level: bool
    model_config = ConfigDict(frozen=True)


class RubyCallableBespokeMarker(BespokeMarker):
    kind: RubyMethodKind
    visibility: RubyVisibilityKind | None
    model_config = ConfigDict(frozen=True)


class RubyClassModuleBespokeMarker(BespokeMarker):
    is_module: bool
    included_modules: tuple[str, ...] | None = None
    extended_modules: tuple[str, ...] | None = None
    prepended_modules: tuple[str, ...] | None = None
    model_config = ConfigDict(frozen=True)


@dataclass
class RubyDriverTree(DriverTree):
    language = "ruby"
    extensions = frozenset([".rb", ".rake", ".gemspec"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "::"
    ) -> str:
        path_parts = []
        current_node = node.parent

        while current_node:
            if current_node.type == "class" or current_node.type == "module":
                name_node = current_node.child_by_field_name("name")
                if name_node:
                    path_parts.append(name_node.text.decode("utf-8"))
            current_node = current_node.parent

        path_parts.reverse()

        return sep.join(path_parts)

    def _extract_requires(self) -> list[RawTreeSitterSymbolData]:
        require_query_str = """
(call
  method: (identifier) @method_name
  arguments: (argument_list
    (string) @required_path)) @require_call
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, require_query_str)
        )
        require_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            method_name = captures_by_name.get("method_name")[0].text.decode("utf-8")

            if method_name not in ("require", "require_relative"):
                continue

            require_node = captures_by_name.get("require_call")[0]
            required_path_node = captures_by_name.get("required_path")[0]
            required_path = required_path_node.text.decode("utf-8")[1:-1]

            is_relative = method_name == "require_relative"

            name = required_path
            if name.endswith(".rb"):
                name = name[:-3]

            start_line = require_node.start_point.row + 1
            end_line = require_node.end_point.row + 1

            bespoke_data = RubyRequireBespokeMarker(is_relative=is_relative)

            symbol = RawTreeSitterSymbolData(
                name=name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.IMPORT,
                start_byte=require_node.start_byte,
                end_byte=require_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path="",
                symbol_code=self.source_bytes[
                    require_node.start_byte : require_node.end_byte
                ].decode("utf-8"),
                delimiter="::",
                bespoke_data=bespoke_data,
            )
            require_list.append(symbol)

        return sorted(require_list, key=lambda x: x.start_byte)

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        return self._extract_requires()

    def _determine_method_visibility(
        self, method_node: tree_sitter.Node
    ) -> RubyVisibilityKind | None:
        visibility_map = {
            "private": RubyVisibilityKind.PRIVATE,
            "protected": RubyVisibilityKind.PROTECTED,
            "public": RubyVisibilityKind.PUBLIC,
        }

        # Check if method is wrapped in a visibility modifier (inline: `private def method`)
        # The method will be in an argument_list of a call node
        parent = method_node.parent
        if parent and parent.type == "argument_list":
            # Check the grandparent for the call node
            grandparent = parent.parent
            if grandparent and grandparent.type == "call":
                # Get the identifier (first child should be the method name)
                for child in grandparent.children:
                    if child.type == "identifier":
                        method_text = child.text.decode("utf-8")
                        if method_text in visibility_map:
                            return visibility_map[method_text]
                        break

        # Check for block-level visibility modifiers
        # Visibility keywords appear as identifier nodes before methods in the body_statement
        # We need to find the most recent visibility modifier before this method
        parent = method_node.parent
        if parent and parent.type == "body_statement":
            # Find the index of the current method in the parent's children
            method_index = None
            for i, child in enumerate(parent.children):
                if child == method_node:
                    method_index = i
                    break

            if method_index is not None:
                # Look backwards through siblings to find the most recent visibility modifier
                for i in range(method_index - 1, -1, -1):
                    sibling = parent.children[i]
                    if sibling.type == "identifier":
                        text = sibling.text.decode("utf-8")
                        if text in visibility_map:
                            return visibility_map[text]

        return None

    def _determine_method_kind(self, method_node: tree_sitter.Node) -> RubyMethodKind:
        """
        Determine if a method is top-level, instance method, class method, or module method.
        """
        # Singleton methods (def self.method) are class/module methods
        if method_node.type == "singleton_method":
            # Check if inside a module or class
            current = method_node.parent
            while current:
                if current.type == "module":
                    return RubyMethodKind.MODULE_METHOD
                if current.type == "class":
                    return RubyMethodKind.CLASS_METHOD
                if current.type == "program":
                    # Singleton method at top level (def self.method at file scope)
                    # Treat as top-level method
                    return RubyMethodKind.TOP_LEVEL
                current = current.parent

            raise ValueError(
                f"Unexpected: singleton method node at line {method_node.start_point.row + 1} "
                "has no parent path to program root"
            )

        # Regular methods - check if inside a class, module, or top-level
        current = method_node.parent
        while current:
            if current.type == "module":
                return RubyMethodKind.INSTANCE_METHOD
            if current.type == "class":
                return RubyMethodKind.INSTANCE_METHOD
            if current.type == "program":
                return RubyMethodKind.TOP_LEVEL
            current = current.parent

        # This should never happen in a valid parse tree
        raise ValueError(
            f"Unexpected: method node at line {method_node.start_point.row + 1} "
            "has no parent path to program root"
        )

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        method_query_str = """
[
  (method
    name: (identifier) @method_name) @method_def
  (singleton_method
    name: (identifier) @method_name) @method_def
]
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, method_query_str)
        )
        method_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            method_node = captures_by_name.get("method_def")[0]
            method_name = captures_by_name.get("method_name")[0].text.decode("utf-8")

            callable_kind = self._determine_method_kind(method_node)

            visibility = self._determine_method_visibility(method_node)

            bespoke_data = RubyCallableBespokeMarker(
                kind=callable_kind, visibility=visibility
            )

            start_line = method_node.start_point.row + 1
            end_line = method_node.end_point.row + 1
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                method_node
            )

            symbol = RawTreeSitterSymbolData(
                name=method_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALLABLE,
                start_byte=method_node.start_byte,
                end_byte=method_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=self.source_bytes[
                    method_node.start_byte : method_node.end_byte
                ].decode("utf-8"),
                delimiter="::",
                bespoke_data=bespoke_data,
            )
            method_list.append(symbol)

        return sorted(method_list, key=lambda x: x.start_byte)

    def _extract_class_and_module_definitions(self) -> list[RawTreeSitterSymbolData]:
        query_str = """
(class
  name: (constant) @name) @definition

(module
  name: (constant) @name) @definition
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, query_str)
        )
        definitions_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            def_node = captures_by_name.get("definition")[0]
            def_name = captures_by_name.get("name")[0].text.decode("utf-8")

            # Use SymbolKind.CLASS for both classes and modules
            # The distinction is tracked in bespoke_data.is_module
            symbol_kind = SymbolKind.CLASS
            is_module = def_node.type == "module"

            # Extract base class (only for classes with inheritance)
            base_class_names = None
            if def_node.type == "class":
                # Look for superclass child node
                superclass_node = None
                for child in def_node.children:
                    if child.type == "superclass":
                        superclass_node = child
                        break

                if superclass_node:
                    # Extract the base class name (handle both simple and namespaced)
                    base_class_name = self._extract_constant_name(
                        superclass_node.children[1]
                    )  # Skip the '<' token
                    base_class_names = (base_class_name,)

            # Extract included, extended, and prepended modules
            (
                included_modules,
                extended_modules,
                prepended_modules,
            ) = self._extract_mixins(def_node)

            bespoke_data = RubyClassModuleBespokeMarker(
                is_module=is_module,
                included_modules=tuple(included_modules) if included_modules else None,
                extended_modules=tuple(extended_modules) if extended_modules else None,
                prepended_modules=tuple(prepended_modules)
                if prepended_modules
                else None,
            )

            start_line = def_node.start_point.row + 1
            end_line = def_node.end_point.row + 1
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                def_node
            )

            symbol = RawTreeSitterSymbolData(
                name=def_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=symbol_kind,
                start_byte=def_node.start_byte,
                end_byte=def_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=self.source_bytes[
                    def_node.start_byte : def_node.end_byte
                ].decode("utf-8"),
                delimiter="::",
                base_class_names=base_class_names,
                bespoke_data=bespoke_data,
            )
            definitions_list.append(symbol)

        return sorted(definitions_list, key=lambda x: x.start_byte)

    def _extract_constant_name(self, node: tree_sitter.Node) -> str:
        if node.type == "constant":
            return node.text.decode("utf-8")
        elif node.type == "scope_resolution":
            # Recursively build the namespaced name
            parts = []
            for child in node.children:
                if child.type == "constant":
                    parts.append(child.text.decode("utf-8"))
                elif child.type == "scope_resolution":
                    parts.append(self._extract_constant_name(child))
            return "::".join(parts)
        else:
            # Fallback: return the raw text
            return node.text.decode("utf-8")

    def _extract_mixins(
        self, class_or_module_node: tree_sitter.Node
    ) -> tuple[list[str], list[str], list[str]]:
        included_modules = []
        extended_modules = []
        prepended_modules = []

        # Find the body_statement node
        body_node = None
        for child in class_or_module_node.children:
            if child.type == "body_statement":
                body_node = child
                break

        if not body_node:
            return [], [], []

        # Iterate through direct children of body_statement
        for child in body_node.children:
            if child.type == "call":
                # Check if this is an include, extend, or prepend call
                method_name = None
                argument_list = None

                for subchild in child.children:
                    if subchild.type == "identifier":
                        method_name = subchild.text.decode("utf-8")
                    elif subchild.type == "argument_list":
                        argument_list = subchild

                if method_name in ["include", "extend", "prepend"] and argument_list:
                    # Extract all module names from the argument list
                    if method_name == "include":
                        target_list = included_modules
                    elif method_name == "extend":
                        target_list = extended_modules
                    else:  # prepend
                        target_list = prepended_modules

                    for arg in argument_list.children:
                        if arg.type in ["constant", "scope_resolution"]:
                            module_name = self._extract_constant_name(arg)
                            # Deduplicate while preserving order
                            if module_name not in target_list:
                                target_list.append(module_name)

        return included_modules, extended_modules, prepended_modules

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        return self._extract_class_and_module_definitions()

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        calls_query_str = """
; Simple method/function calls (no receiver)
(call
  method: (identifier) @call_name) @call

; Method calls with receiver (object.method)
(call
  receiver: (_)
  method: (identifier) @call_name) @call

; Super calls
(super) @call

; Yield calls
(yield) @call
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, calls_query_str)
        )
        calls_list = []

        for pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            call_node = captures_by_name.get("call")[0]

            if pattern_idx in [0, 1]:  # Regular calls
                call_name_node = captures_by_name.get("call_name")
                if not call_name_node:
                    continue
                call_name = call_name_node[0].text.decode("utf-8")
            elif pattern_idx == 2:  # super
                call_name = "super"
            elif pattern_idx == 3:  # yield
                call_name = "yield"
            else:
                continue

            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                call_node
            )

            start_line = call_node.start_point.row + 1
            end_line = call_node.end_point.row + 1

            symbol = RawTreeSitterSymbolData(
                name=call_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.CALL,
                start_byte=call_node.start_byte,
                end_byte=call_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=self.source_bytes[
                    call_node.start_byte : call_node.end_byte
                ].decode("utf-8"),
                delimiter="::",
                bespoke_data=None,
            )
            calls_list.append(symbol)

        return sorted(calls_list, key=lambda x: x.start_byte)

    def _extract_variables_and_constants(self) -> list[RawTreeSitterSymbolData]:
        variable_query_str = """
; Single variable assignment
(assignment
  left: [
    (constant) @var_name
    (instance_variable) @var_name
    (class_variable) @var_name
    (global_variable) @var_name
  ]) @assignment

; Parallel/multiple assignment (@x, @y = 0, 0)
(assignment
  left: (left_assignment_list
    [
      (constant) @var_name
      (instance_variable) @var_name
      (class_variable) @var_name
      (global_variable) @var_name
    ])) @assignment
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, variable_query_str)
        )

        # Track seen variables by (name, fqp) to deduplicate
        seen_variables = set()
        variable_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            var_name_node = captures_by_name.get("var_name")[0]
            assignment_node = captures_by_name.get("assignment")[0]

            var_name = var_name_node.text.decode("utf-8")

            if var_name.startswith("@@"):
                var_kind = RubyVariableKind.VARIABLE  # Class variable
            elif var_name.startswith("@"):
                var_kind = RubyVariableKind.VARIABLE  # Instance variable
            elif var_name.startswith("$"):
                var_kind = RubyVariableKind.VARIABLE  # Global variable
            elif var_name[0].isupper():
                var_kind = RubyVariableKind.CONSTANT
            else:
                # Lowercase variables are local, skip them
                continue

            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                assignment_node
            )

            is_top_level = fully_qualified_parent_path == ""

            dedup_key = (var_name, fully_qualified_parent_path)

            if dedup_key in seen_variables:
                continue

            seen_variables.add(dedup_key)

            bespoke_data = RubyVariableBespokeMarker(
                kind=var_kind, is_top_level=is_top_level, access=None
            )

            start_line = assignment_node.start_point.row + 1
            end_line = assignment_node.end_point.row + 1

            symbol = RawTreeSitterSymbolData(
                name=var_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.VARIABLE_DEFINITION,
                start_byte=assignment_node.start_byte,
                end_byte=assignment_node.end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=self.source_bytes[
                    assignment_node.start_byte : assignment_node.end_byte
                ].decode("utf-8"),
                delimiter="::",
                bespoke_data=bespoke_data,
            )
            variable_list.append(symbol)

        return sorted(variable_list, key=lambda x: x.start_byte)

    def _extract_attributes(self) -> list[RawTreeSitterSymbolData]:
        attribute_query_str = """
(call
  method: (identifier) @method_name
  arguments: (argument_list
    (simple_symbol) @attr_name)) @attr_call
        """.strip()

        query_cursor = tree_sitter.QueryCursor(
            tree_sitter.Query(self.tree_sitter_lang, attribute_query_str)
        )

        attribute_list = []

        for _pattern_idx, captures_by_name in query_cursor.matches(self.tree.root_node):
            method_name_node = captures_by_name.get("method_name")
            if not method_name_node:
                continue

            method_name = method_name_node[0].text.decode("utf-8")

            if method_name == "attr_accessor":
                access_mode = RubyAttributeAccessKind.READ_WRITE
            elif method_name == "attr_reader":
                access_mode = RubyAttributeAccessKind.READ
            elif method_name == "attr_writer":
                access_mode = RubyAttributeAccessKind.WRITE
            else:
                continue

            attr_call_node = captures_by_name.get("attr_call")[0]
            attr_name_nodes = captures_by_name.get("attr_name")

            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                attr_call_node
            )

            # Process each attribute name in the call
            # (attr_accessor :name, :age creates two separate attributes)
            for attr_name_node in attr_name_nodes:
                attr_name_raw = attr_name_node.text.decode("utf-8")
                # Remove leading colon from symbol
                attr_name = attr_name_raw.lstrip(":")
                # Remove quotes if present (:"name" -> name)
                attr_name = attr_name.strip("\"'")

                bespoke_data = RubyVariableBespokeMarker(
                    kind=RubyVariableKind.ATTRIBUTE,
                    access=access_mode,
                    is_top_level=False,
                )

                # Use the attr_call node's location for all attributes in this call
                start_line = attr_call_node.start_point.row + 1
                end_line = attr_call_node.end_point.row + 1

                symbol = RawTreeSitterSymbolData(
                    name=attr_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.VARIABLE_DEFINITION,
                    start_byte=attr_call_node.start_byte,
                    end_byte=attr_call_node.end_byte,
                    file_path=self.file_path,
                    fully_qualified_parent_path=fully_qualified_parent_path,
                    symbol_code=self.source_bytes[
                        attr_call_node.start_byte : attr_call_node.end_byte
                    ].decode("utf-8"),
                    delimiter="::",
                    bespoke_data=bespoke_data,
                )
                attribute_list.append(symbol)

        return sorted(attribute_list, key=lambda x: (x.start_byte, x.name))

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return self._extract_variables_and_constants() + self._extract_attributes()

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []
