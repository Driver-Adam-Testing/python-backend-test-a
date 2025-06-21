from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import Self

import tree_sitter

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData, SymbolKind

from .base import DriverTree


class CSharpCallKind(StrEnum):
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    OP_OVERLOAD = "operator_overload"
    CONVERSION = "conversion_operator_declaration"
    LOCAL_FN = "local_function"
    PROPERTY = "property"


class CSharpMethodModifier(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    VIRTUAL = "virtual"
    OVERRIDE = "override"
    ABSTRACT = "abstract"
    SEALED = "sealed"
    STATIC = "static"
    ASYNC = "async"
    EXTERN = "extern"
    UNSAFE = "unsafe"
    IMPLICIT = "implicit"
    EXPLICIT = "explicit"

    @classmethod
    def from_str(cls, candidate: str) -> Self | None:
        return _method_modifier_lookup().get(candidate)


class CSharpClassModifier(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
    PROTECTED = "protected"
    ABSTRACT = "abstract"
    SEALED = "sealed"
    STATIC = "static"
    PARTIAL = "partial"
    UNSAFE = "unsafe"

    @classmethod
    def from_str(cls, candidate: str) -> Self | None:
        return _class_modifier_lookup().get(candidate)


@cache
def _method_modifier_lookup() -> dict[str, CSharpMethodModifier]:
    return {m.value: m for m in CSharpMethodModifier}


@cache
def _class_modifier_lookup() -> dict[str, CSharpClassModifier]:
    return {m.value: m for m in CSharpClassModifier}


def cs_node_to_text(source_bytes: bytes, node: tree_sitter.Node) -> str:
    start = node.start_byte
    end = node.end_byte

    return source_bytes[start:end].decode("utf-8")


def _extract_namespace_name(name_node: tree_sitter.Node, sep: str = ".") -> str:
    """Recursively extract full namespace name from a qualified_name node."""
    if name_node.type == "qualified_name":
        # Example: System.Collections.Generic
        parts = []
        for child in name_node.children:
            if child.type == "identifier":
                parts.append(child.text.decode("utf-8"))
        return sep.join(parts)
    elif name_node.type == "identifier":
        return name_node.text.decode("utf-8")
    return ""


@dataclass
class CSharpDriverTree(DriverTree):
    language = "csharp"
    extensions = frozenset([".cs"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        path_parts = []
        current = node.parent

        while current:
            if current.type == "compilation_unit":
                path_parts.append(str(self.file_path.with_suffix("")))
            elif current.type in {
                "class_declaration",
                "struct_declaration",
                "interface_declaration",
                "method_declaration",
            }:
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(name_node.text.decode("utf-8"))
            elif current.type == "namespace_declaration":
                # Namespace may be nested or qualified
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(
                        _extract_namespace_name(name_node=name_node, sep=sep)
                    )
            current = current.parent

        path_parts.reverse()
        return sep.join(path_parts)

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = "(using_directive) @using_stmt"
        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for _pat_idx, captures_by_name in matches:
            im_node = captures_by_name["using_stmt"][0]
            start_line, end_line = self.get_node_line_range(im_node)
            start_byte, end_byte = im_node.start_byte, im_node.end_byte
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                node=im_node
            )

            resolved_name = False
            alias_name = None

            # Detect if an alias is used up front
            alias_used = False
            for child in im_node.children:
                if child.type == "=":
                    alias_used = True

            # Handle easy signal -- presence of a qualified name without an alias
            if not resolved_name and not alias_used:
                for child in im_node.children:
                    if child.type == "qualified_name":
                        name = child.text.decode("utf-8")
                        resolved_name = True
                        break

            # Handle cases where a qualified name isn't present or presence of an alias
            # E.g., for `using System;` or `using Sys = System;`
            if not resolved_name:
                identifiers = []
                for child in im_node.children:
                    if child.type == "identifier" or child.type == "qualified_name":
                        identifiers.append(child.text.decode("utf-8"))
                        if not alias_used:
                            break
                    elif child.type == "=":
                        identifiers.append("=")

                if alias_used:
                    split_idx = identifiers.index("=")
                    alias_name = identifiers[split_idx - 1]
                    name = identifiers[split_idx + 1]
                    resolved_name = True
                else:
                    if len(identifiers) > 0:
                        name = identifiers[0]
                        resolved_name = True

            if not resolved_name:
                print(f"Unable to resolve import for {im_node.text.decode('utf-8')}")
                name = None

            im = RawTreeSitterSymbolData(
                name=name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=SymbolKind.IMPORT,
                start_byte=start_byte,
                end_byte=end_byte,
                file_path=self.file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                symbol_code=cs_node_to_text(self.source_bytes, im_node),
                delimiter=".",
                lang_specific_data={"alias": alias_name},
            )
            imports.append(im)

        return imports

    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        return self.extract_method_like_definitions()

    def extract_method_like_definitions(self) -> list[RawTreeSitterSymbolData]:
        method_query_str = """
        (method_declaration
          name: (identifier) @method_name) @method

        (constructor_declaration
          name: (identifier) @constructor_name) @constructor

        (destructor_declaration
          name: (identifier) @destructor_name) @destructor

        (operator_declaration) @operator_overload

        (conversion_operator_declaration) @conversion_operator

        (local_function_statement
          name: (identifier) @local_function_name) @local_function

        (property_declaration
          name: (identifier) @property_name) @property
        """.strip()
        query = self.tree_sitter_lang.query(method_query_str)
        matches = query.matches(self.tree.root_node)
        method_likes = []

        for pattern_idx, captures_by_name in matches:
            callable_name = None
            callable_node = None
            modifier_list = []
            lang_specific_data = dict()
            match pattern_idx:
                case 0:  # standard method
                    callable_name = captures_by_name.get("method_name")[0].text.decode(
                        "utf-8"
                    )
                    callable_node = captures_by_name.get("method")[0]
                    callable_kind = CSharpCallKind.METHOD
                case 1:  # constructor
                    callable_name = captures_by_name.get("constructor_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("constructor")[0]
                    callable_kind = CSharpCallKind.CONSTRUCTOR
                case 2:  # destructor
                    # TODO: Should I do this? Keeping the tilde for visual convenience.
                    callable_name = "~" + captures_by_name.get("destructor_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("destructor")[0]
                    callable_kind = CSharpCallKind.DESTRUCTOR
                case 3:  # operator_overload
                    callable_node = captures_by_name.get("operator_overload")[0]
                    children = list(callable_node.children)
                    op_idx = None
                    for idx, child in enumerate(children):
                        if child.type == "operator":
                            op_idx = idx
                            break
                    callable_name = (
                        children[op_idx + 1].text.decode("utf-8") if op_idx else None
                    )
                    callable_kind = CSharpCallKind.OP_OVERLOAD
                    if op_idx:
                        lang_specific_data["op_overload_return_ty"] = children[
                            op_idx - 1
                        ].text.decode("utf-8")
                case 4:  # conversion (implicit and explicit)
                    callable_node = captures_by_name.get("conversion_operator")[0]
                    children = list(callable_node.children)
                    op_idx = None
                    for idx, child in enumerate(children):
                        if child.type == "operator":
                            op_idx = idx
                            break
                    callable_name = (
                        children[op_idx + 1].text.decode("utf-8") if op_idx else None
                    )
                    callable_kind = CSharpCallKind.CONVERSION
                case 5:  # local functions
                    callable_name = captures_by_name.get("local_function_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("local_function")[0]
                    callable_kind = CSharpCallKind.LOCAL_FN
                case 6:  # property
                    callable_name = captures_by_name.get("property_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("property")[0]
                    callable_kind = CSharpCallKind.PROPERTY
                case _:
                    print(f"Unhandled method-like pattern idx: {pattern_idx}")
            if callable_name and callable_node:
                for child in callable_node.children:
                    try:
                        child_name = child.text.decode("utf-8")
                        modifier = CSharpMethodModifier.from_str(child_name)
                        if modifier:
                            modifier_list.append(modifier)
                    except Exception:
                        pass
                start_line, end_line = self.get_node_line_range(callable_node)
                start_byte, end_byte = callable_node.start_byte, callable_node.end_byte
                file_path = self.file_path
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    callable_node
                )
                symbol_code = cs_node_to_text(
                    source_bytes=self.source_bytes, node=callable_node
                )
                symbol_kind = SymbolKind.CALLABLE
                file_path = self.file_path
                delimiter = "."
                lang_specific_data = {
                    **lang_specific_data,
                    "modifiers": modifier_list,
                    "callable_kind": callable_kind,
                }
                method_like = RawTreeSitterSymbolData(
                    name=callable_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=symbol_kind,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    file_path=file_path,
                    fully_qualified_parent_path=fully_qualified_parent_path,
                    symbol_code=symbol_code,
                    delimiter=delimiter,
                    lang_specific_data=lang_specific_data,
                )
                method_likes.append(method_like)
            else:
                print(
                    f"Missing callable name ({callable_name}) or node ({callable_node})"
                )

        return method_likes

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
        klass_query_str = """
        (class_declaration
          name: (identifier) @class_name) @class_def
        """.strip()
        query = self.tree_sitter_lang.query(klass_query_str)
        matches = query.matches(self.tree.root_node)
        klasses = []

        for _pat_idx, captures_by_name in matches:
            klass_node = captures_by_name["class_def"][0]
            klass_name = captures_by_name["class_name"][0]
            if klass_name is None:
                print(f"Could not parse class name for node: {klass_node}")
            else:
                klass_name = klass_name.text.decode("utf-8")
            base_class_names = None
            modifier_list = []
            for child in klass_node.children:
                if child.type == "base_list":
                    base_class_names = []
                    for base in child.children:
                        if base.type in {
                            "identifier",
                            "qualified_name",
                            "generic_name",
                            "invocation_expression",
                        }:
                            base_class_names.append(base.text.decode("utf-8"))
                else:
                    try:
                        child_name = child.text.decode("utf-8")
                        modifier = CSharpClassModifier.from_str(child_name)
                        if modifier:
                            modifier_list.append(modifier)
                    except Exception:
                        pass

            if klass_node and klass_name:
                start_line, end_line = self.get_node_line_range(klass_node)
                start_byte, end_byte = klass_node.start_byte, klass_node.end_byte
                symbol_code = cs_node_to_text(self.source_bytes, klass_node)
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    node=klass_node
                )
                delimiter = "."
                lang_specific_data = {"modifiers": modifier_list}
                klass = RawTreeSitterSymbolData(
                    name=klass_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.CLASS,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    file_path=self.file_path,
                    fully_qualified_path_to_parent=fully_qualified_parent_path,
                    base_class_names=base_class_names,
                    symbol_code=symbol_code,
                    delimiter=delimiter,
                    lang_specific_data=lang_specific_data,
                )
                klasses.append(klass)
            else:
                print(f"Missing class name ({klass_name}) or node ({klass_node})")

        sorted_klasses = sorted(klasses, key=lambda x: x.start_byte)
        return sorted_klasses
