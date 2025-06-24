import re
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from typing import Self

import tree_sitter

from utils.lang_specialization.symbol_common import (
    BespokeMarker,
    RawTreeSitterSymbolData,
    SymbolKind,
)

from .base import DriverTree

GENERICS_PARSER = re.compile(r"<[^>]+>$")


class CSharpImportScopeKind(StrEnum):
    LOCAL_USING = "local_using"
    GLOBAL_USING = "global_using"
    NAMESPACE_DECLARATION = "namespace_declaration"


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


class CSharpClassKind(StrEnum):
    STANDARD = "standard"
    RECORD = "record"


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


class CSharpDataStructureKind(StrEnum):
    ENUM = "enum"
    STRUCT = "struct"
    RECORD_STRUCT = "record_struct"


class CSharpDataStructureModifier(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    READONLY = "readonly"
    STATIC = "static"
    PARTIAL = "partial"
    UNSAFE = "unsafe"
    # NOTE: `ref` is a keyword not modifier in C#. Using "our own definition of modifier" here
    REF = "ref"
    RECORD = "record"

    @classmethod
    def from_str(cls, candidate: str) -> Self | None:
        return _data_structure_modifier_lookup().get(candidate)


@cache
def _method_modifier_lookup() -> dict[str, CSharpMethodModifier]:
    return {m.value: m for m in CSharpMethodModifier}


@cache
def _class_modifier_lookup() -> dict[str, CSharpClassModifier]:
    return {m.value: m for m in CSharpClassModifier}


@cache
def _data_structure_modifier_lookup() -> dict[str, CSharpDataStructureModifier]:
    return {m.value: m for m in CSharpDataStructureModifier}


class CSharpImportsData(BespokeMarker):
    scoping_kind: CSharpImportScopeKind
    alias_name: str | None


class CSharpMethodLikeData(BespokeMarker):
    kind: CSharpCallKind
    modifiers: list[CSharpMethodModifier]
    op_overload_return_ty: str | None


class CSharpDataStructureData(BespokeMarker):
    kind: CSharpDataStructureKind
    modifiers: list[CSharpDataStructureModifier]
    underlying_ty: str | None


class CSharpClassData(BespokeMarker):
    kind: CSharpClassKind
    modifiers: list[CSharpClassModifier]


def cs_node_to_text(source_bytes: bytes, node: tree_sitter.Node) -> str:
    start = node.start_byte
    end = node.end_byte

    return source_bytes[start:end].decode("utf-8")


@dataclass
class CSharpDriverTree(DriverTree):
    language = "csharp"
    extensions = frozenset([".cs"])

    def _get_fully_qualified_path_to_parent(
        self, node: tree_sitter.Node, sep: str = "."
    ) -> str:
        path_parts = []
        current = node.parent

        # TODO: Consider detecting implicit global namespacing (no namespace declared)
        # and adding `global::` to the FQN, in line with C# syntax. The problem is,
        # though, `using` imports that are implicitly using the global namespace (cf.,
        # explicitly doing so with `global::` need to be detected to properly match.
        # I don't think we need to do this for rigorous linking/matching, but it could
        # help us document `global` usage explicitly downstream.
        while current:
            if current.type == "compilation_unit":
                break
            elif current.type in {
                "class_declaration",
                "struct_declaration",
                "enum_declaration",
                "interface_declaration",
                "delegate_declaration",
                "method_declaration",
            }:
                name_node = current.child_by_field_name("name")
                if name_node:
                    path_parts.append(name_node.text.decode("utf-8"))
            elif current.type == "namespace_declaration":
                path_parts.append(
                    current.child_by_field_name("name").text.decode("utf-8")
                )
            current = current.parent

        path_parts.reverse()
        return sep.join(path_parts)

    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        using_imports = self.extract_using_imports()
        namespace_imports = self.extract_namespace_declarations()
        return using_imports + namespace_imports

    def extract_using_imports(self) -> list[RawTreeSitterSymbolData]:
        import_query_str = "(using_directive) @using_stmt"
        query = self.tree_sitter_lang.query(import_query_str)
        matches = query.matches(self.tree.root_node)
        imports = []

        for _pat_idx, captures_by_name in matches:
            im_node = captures_by_name["using_stmt"][0]
            resolved_name = False
            alias_name = None

            # Detect if `global using` is used.
            is_global_using = False
            for child in im_node.children:
                if child.type == "global":
                    is_global_using = True
                    break

            # Detect if an alias is used up front
            alias_used = False
            for child in im_node.children:
                if child.type == "=":
                    alias_used = True
                    break

            # Handle easy signal -- presence of a qualified name without an alias
            if not resolved_name and not alias_used:
                for child in im_node.children:
                    if child.type == "qualified_name":
                        # name = child.child_by_field_name("name").text.decode("utf-8")
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

            start_line, end_line = self.get_node_line_range(im_node)
            start_byte, end_byte = im_node.start_byte, im_node.end_byte
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                node=im_node
            )
            scoping_kind = (
                CSharpImportScopeKind.GLOBAL_USING
                if is_global_using
                else CSharpImportScopeKind.LOCAL_USING
            )
            bespoke_data = CSharpImportsData(
                scoping_kind=scoping_kind, alias_name=alias_name
            )

            # TODO: Detect generic parameters and pass as metadata?
            # TODO: E.g., `Dictionary<string, object>` being imported.
            # TODO: Here we just report `Dictionary`
            name = GENERICS_PARSER.sub("", name)

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
                bespoke_data=bespoke_data,
            )
            imports.append(im)

        return imports

    def extract_namespace_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

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
            op_overload_return_ty = None
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
                        op_overload_return_ty = children[op_idx - 1].text.decode(
                            "utf-8"
                        )
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
                bespoke_data = CSharpMethodLikeData(
                    kind=callable_kind,
                    modifiers=modifier_list,
                    op_overload_return_ty=op_overload_return_ty,
                )
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
                    bespoke_data=bespoke_data,
                )
                method_likes.append(method_like)
            else:
                print(
                    f"Missing callable name ({callable_name}) or node ({callable_node})"
                )

        return method_likes

    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        enums = self.extract_enum_definitions()
        structs = self.extract_struct_definitions()
        return enums + structs

    def extract_enum_definitions(self) -> list[RawTreeSitterSymbolData]:
        enum_query_str = """
        (enum_declaration
          (modifier)* @enum_modifier
          name: (identifier) @enum_name) @enum
        """.strip()
        query = self.tree_sitter_lang.query(enum_query_str)
        matches = query.matches(self.tree.root_node)
        enums = []

        for _pat_idx, captures_by_name in matches:
            enum_node = captures_by_name["enum"][0]
            enum_name = captures_by_name["enum_name"][0].text.decode("utf-8")
            enum_modifiers = captures_by_name["enum_modifier"]
            modifier_list = []
            for m in enum_modifiers:
                modifier = CSharpDataStructureModifier.from_str(m.text.decode("utf-8"))
                if modifier:
                    modifier_list.append(modifier)

            # TODO: Consider moving this to be lang-specific.
            # TODO: `base_class_names` is a misnomer as this includes interfaces.
            base_class_names = None
            underlying_ty = "default"
            for child in enum_node.children:
                if child.type == "base_list":
                    # You can specify a different underlying type for an `enum`, but it
                    # must be the first item in the base list after `:` (index 0).
                    try:
                        if child.children[1].type == "predefined_type":
                            underlying_ty = child.children[1].text.decode("utf-8")
                    except Exception:
                        pass
                    base_class_names = []
                    for base in child.children:
                        # TODO: Think about this -- needs to match what is extracted for
                        # TODO: `interface`s to make links (e.g., Interface or Interface<T>)
                        # TODO: Unify with solution in extracting interfaces.
                        if base.type in {
                            "identifier",
                            "qualified_name",
                            "generic_name",
                            "invocation_expression",
                        }:
                            base_class_names.append(base.text.decode("utf-8"))

            start_line, end_line = self.get_node_line_range(enum_node)
            start_byte, end_byte = enum_node.start_byte, enum_node.end_byte
            file_path = self.file_path
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                enum_node
            )
            symbol_code = cs_node_to_text(
                source_bytes=self.source_bytes, node=enum_node
            )
            symbol_kind = SymbolKind.DATA_STRUCTURE
            file_path = self.file_path
            delimiter = "."
            bespoke_data = CSharpDataStructureData(
                kind=CSharpDataStructureKind.ENUM,
                modifiers=modifier_list,
                underlying_ty=underlying_ty,
            )
            enum = RawTreeSitterSymbolData(
                name=enum_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=symbol_kind,
                start_byte=start_byte,
                end_byte=end_byte,
                file_path=file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                base_class_names=base_class_names,
                symbol_code=symbol_code,
                delimiter=delimiter,
                bespoke_data=bespoke_data,
            )
            enums.append(enum)

        return enums

    def extract_struct_definitions(self) -> list[RawTreeSitterSymbolData]:
        struct_query_str = """
        [
          (struct_declaration
            (modifier)* @struct_modifier
            name: (identifier) @struct_name)

          (record_declaration
            (modifier)* @struct_modifier
            name: (identifier) @record_name)
        ] @struct_def
        """.strip()
        query = self.tree_sitter_lang.query(struct_query_str)
        matches = query.matches(self.tree.root_node)
        structs = []

        for _pat_idx, captures_by_name in matches:
            struct_node = captures_by_name["struct_def"][0]
            is_record_struct = False
            if "record_name" in captures_by_name:
                if any(child.type == "struct" for child in struct_node.children):
                    is_record_struct = True
                else:
                    # Skip `record`s (reference types -- parsed with classes)
                    continue
            is_ref = any(child.type == "ref" for child in struct_node.children)
            struct_name = (
                captures_by_name["record_name"][0]
                if is_record_struct
                else captures_by_name["struct_name"][0]
            )
            if struct_name is None:
                print(f"Could not parse class name for node: {struct_node}")
            else:
                struct_name = struct_name.text.decode("utf-8")
            modifier_list = [CSharpDataStructureModifier.REF] if is_ref else []
            struct_modifiers = captures_by_name["struct_modifier"]
            for m in struct_modifiers:
                modifier = CSharpDataStructureModifier.from_str(m.text.decode("utf-8"))
                if modifier:
                    modifier_list.append(modifier)

            # TODO: Consider moving this to be lang-specific.
            # TODO: `base_class_names` is a misnomer as this includes interfaces.
            base_class_names = None
            for child in struct_node.children:
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

            start_line, end_line = self.get_node_line_range(struct_node)
            start_byte, end_byte = struct_node.start_byte, struct_node.end_byte
            file_path = self.file_path
            fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                struct_node
            )
            symbol_code = cs_node_to_text(
                source_bytes=self.source_bytes, node=struct_node
            )
            symbol_kind = SymbolKind.DATA_STRUCTURE
            file_path = self.file_path
            delimiter = "."
            bespoke_data = CSharpDataStructureData(
                kind=CSharpDataStructureKind.RECORD_STRUCT
                if is_record_struct
                else CSharpDataStructureKind.STRUCT,
                modifiers=modifier_list,
                underlying_ty=None,
            )
            struct = RawTreeSitterSymbolData(
                name=struct_name,
                start_line=start_line,
                end_line=end_line,
                symbol_kind=symbol_kind,
                start_byte=start_byte,
                end_byte=end_byte,
                file_path=file_path,
                fully_qualified_parent_path=fully_qualified_parent_path,
                base_class_names=base_class_names,
                symbol_code=symbol_code,
                delimiter=delimiter,
                bespoke_data=bespoke_data,
            )
            structs.append(struct)

        return structs

    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        return []

    def extract_class_definitions(self) -> list[RawTreeSitterSymbolData]:
        klass_query_str = """
        [
          (class_declaration
            name: (identifier) @class_name)
          (record_declaration
            name: (identifier) @record_name)
        ] @class_def
        """.strip()
        query = self.tree_sitter_lang.query(klass_query_str)
        matches = query.matches(self.tree.root_node)
        klasses = []

        for _pat_idx, captures_by_name in matches:
            klass_node = captures_by_name["class_def"][0]
            # Note: C# distinguishes the `struct`/`class` dichotomy in terms of reference types
            # Note: (reference semantics, behind a pointer on the heap) and value types (value
            # Note: semantics, entire value copy, value equality, on the stack by default).
            # Note: Classes are reference types and structs are value types. We organize our
            # Note: documentation accordingly, letting `record`s live with classes and
            # Note: `recort struct`s live with data structures.
            is_record = "record_name" in captures_by_name
            klass_name = (
                captures_by_name["record_name"][0]
                if is_record
                else captures_by_name["class_name"][0]
            )
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
                class_kind = (
                    CSharpClassKind.RECORD if is_record else CSharpClassKind.STANDARD
                )
                bespoke_data = CSharpClassData(kind=class_kind, modifiers=modifier_list)
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
                    bespoke_data=bespoke_data,
                )
                klasses.append(klass)
            else:
                print(f"Missing class name ({klass_name}) or node ({klass_node})")

        sorted_klasses = sorted(klasses, key=lambda x: x.start_byte)
        return sorted_klasses

    def extract_interfaces(self) -> list[RawTreeSitterSymbolData]:
        return []
