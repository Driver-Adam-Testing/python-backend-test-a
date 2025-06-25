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
    NAMESPACE_BLOCK_SCOPE_DECL = "namespace_block_scope_declaration"
    NAMESPACE_FILE_SCOPE_DECL = "namespace_file_scope_declaration"


class CSharpCallKind(StrEnum):
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    OP_OVERLOAD = "operator_overload"
    CONVERSION = "conversion_operator_declaration"
    LOCAL_FN = "local_function"
    PROPERTY = "property"
    INDEXER = "indexer"
    EVENT_FIELD_LIKE = "event_field_like"
    EVENT_PROPERTY_LIKE = "event_property_like"


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


class CSharpInterfaceModifier(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    UNSAFE = "unsafe"
    PARTIAL = "partial"
    PROTECTED = "protected"

    @classmethod
    def from_str(cls, candidate: str) -> Self | None:
        return _interface_modifier_lookup().get(candidate)


@cache
def _method_modifier_lookup() -> dict[str, CSharpMethodModifier]:
    return {m.value: m for m in CSharpMethodModifier}


@cache
def _class_modifier_lookup() -> dict[str, CSharpClassModifier]:
    return {m.value: m for m in CSharpClassModifier}


@cache
def _data_structure_modifier_lookup() -> dict[str, CSharpDataStructureModifier]:
    return {m.value: m for m in CSharpDataStructureModifier}


@cache
def _interface_modifier_lookup() -> dict[str, CSharpInterfaceModifier]:
    return {m.value: m for m in CSharpInterfaceModifier}


class CSharpImportData(BespokeMarker):
    scoping_kind: CSharpImportScopeKind
    alias_name: str | None


class CSharpMethodLikeData(BespokeMarker):
    kind: CSharpCallKind
    modifiers: list[CSharpMethodModifier]
    return_ty: str | None


class CSharpDataStructureData(BespokeMarker):
    kind: CSharpDataStructureKind
    modifiers: list[CSharpDataStructureModifier]
    underlying_ty: str | None


class CSharpClassData(BespokeMarker):
    kind: CSharpClassKind
    modifiers: list[CSharpClassModifier]


class CSharpInterfaceData(BespokeMarker):
    base_names: list[str]
    modifiers: list[CSharpInterfaceModifier]
    type_params: list[str]


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

    def extract_all_symbols(self) -> list[RawTreeSitterSymbolData]:
        """Extract all symbols from the source code."""
        symbols = []
        symbols.extend(self.extract_imports())
        symbols.extend(self.extract_callable_definitions())
        symbols.extend(self.extract_data_structure_definitions())
        symbols.extend(self.extract_class_definitions())
        symbols.extend(self.extract_interfaces())
        symbols.extend(self.extract_function_calls())
        return symbols

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
            bespoke_data = CSharpImportData(
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

        sorted_imports = sorted(imports, key=lambda x: x.start_byte)
        return sorted_imports

    def extract_namespace_declarations(self) -> list[RawTreeSitterSymbolData]:
        namespace_query_str = """
        (namespace_declaration
          name: (qualified_name) @namespace_name) @block_namespace

        (file_scoped_namespace_declaration
          name: (qualified_name) @namespace_name) @file_namespace
        """.strip()

        query = self.tree_sitter_lang.query(namespace_query_str)
        matches = query.matches(self.tree.root_node)
        namespaces = []

        for pattern_idx, captures_by_name in matches:
            match pattern_idx:
                case 0:  # block-scoped namespace declaration
                    namespace_name = captures_by_name.get("namespace_name")[
                        0
                    ].text.decode("utf-8")
                    namespace_node = captures_by_name.get("block_namespace")[0]
                    namespace_kind = CSharpImportScopeKind.NAMESPACE_BLOCK_SCOPE_DECL
                case 1:  # file-scoped namespace declaration
                    namespace_name = captures_by_name.get("namespace_name")[
                        0
                    ].text.decode("utf-8")
                    namespace_node = captures_by_name.get("file_namespace")[0]
                    namespace_kind = CSharpImportScopeKind.NAMESPACE_FILE_SCOPE_DECL
                case _:
                    raise ValueError("Unreachable")

            if namespace_name and namespace_node:
                start_line, end_line = self.get_node_line_range(namespace_node)
                start_byte, end_byte = (
                    namespace_node.start_byte,
                    namespace_node.end_byte,
                )
                file_path = self.file_path
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    namespace_node
                )
                symbol_code = cs_node_to_text(
                    source_bytes=self.source_bytes, node=namespace_node
                )
                symbol_kind = SymbolKind.IMPORT
                file_path = self.file_path
                delimiter = "."
                bespoke_data = CSharpImportData(
                    scoping_kind=namespace_kind, alias_name=None
                )
                namespace = RawTreeSitterSymbolData(
                    name=namespace_name,
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
                namespaces.append(namespace)
            else:
                print(
                    f"Missing callable name ({namespace_name}) or node ({namespace_node})"
                )

        sorted_namespaces = sorted(namespaces, key=lambda x: x.start_byte)
        return sorted_namespaces

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

        (indexer_declaration) @indexer

        (event_declaration
          name: (identifier) @event_property_like_name) @event_property_like

        (event_field_declaration) @event_field_like
        """.strip()
        query = self.tree_sitter_lang.query(method_query_str)
        matches = query.matches(self.tree.root_node)
        method_likes = []

        for pattern_idx, captures_by_name in matches:
            callable_name = None
            callable_node = None
            modifier_list = []
            return_ty = None
            match pattern_idx:
                case 0:  # standard method
                    callable_name = captures_by_name.get("method_name")[0].text.decode(
                        "utf-8"
                    )
                    callable_node = captures_by_name.get("method")[0]
                    callable_kind = CSharpCallKind.METHOD
                    return_ty = None
                case 1:  # constructor
                    callable_name = captures_by_name.get("constructor_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("constructor")[0]
                    callable_kind = CSharpCallKind.CONSTRUCTOR
                    return_ty = None
                case 2:  # destructor
                    # TODO: Should I do this? Keeping the tilde for visual convenience.
                    callable_name = "~" + captures_by_name.get("destructor_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("destructor")[0]
                    callable_kind = CSharpCallKind.DESTRUCTOR
                    return_ty = None
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
                        return_ty = children[op_idx - 1].text.decode("utf-8")
                    else:
                        return_ty = None
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
                    return_ty = None
                case 5:  # local functions
                    callable_name = captures_by_name.get("local_function_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("local_function")[0]
                    callable_kind = CSharpCallKind.LOCAL_FN
                    return_ty = None
                case 6:  # property
                    callable_name = captures_by_name.get("property_name")[
                        0
                    ].text.decode("utf-8")
                    callable_node = captures_by_name.get("property")[0]
                    callable_kind = CSharpCallKind.PROPERTY
                    return_ty = None
                case 7:  # indexer
                    callable_node = captures_by_name.get("indexer")[0]
                    callable_name = None
                    callable_kind = CSharpCallKind.INDEXER
                    children = list(callable_node.children)
                    this_idx = None
                    return_ty = None
                    for idx, child in enumerate(children):
                        if child.type == "bracketed_parameter_list":
                            callable_name = child.text.decode("utf-8")
                        if child.type == "this":
                            this_idx = idx
                    if this_idx:
                        return_ty = children[this_idx - 1].text.decode("utf-8")
                case 8:  # property-like event
                    # TODO: Consider parsing the `accessor_list` that may be present
                    callable_node = captures_by_name.get("event_property_like")[0]
                    callable_name = captures_by_name.get("event_property_like_name")[
                        0
                    ].text.decode("utf-8")
                    callable_kind = CSharpCallKind.EVENT_PROPERTY_LIKE
                    children = list(callable_node.children)
                    return_ty_idx = None
                    for idx, child in enumerate(children):
                        if child.type == "event":
                            return_ty_idx = idx + 1
                            break
                    return_ty = children[return_ty_idx].text.decode("utf-8")
                case 9:  # field-like event
                    callable_node = captures_by_name.get("event_field_like")[0]
                    callable_name = None
                    callable_kind = CSharpCallKind.EVENT_FIELD_LIKE
                    return_ty = None
                    children = list(callable_node.children)
                    # TODO this seems very fragile; not sure if this works in all cases
                    event_idx = None
                    for idx, child in enumerate(children):
                        if child.type == "event":
                            event_idx = idx
                    event_info = children[event_idx + 1]
                    if event_idx and event_info.type == "variable_declaration":
                        return_ty = event_info.children[0].text.decode("utf-8")
                        callable_name = event_info.children[1].text.decode("utf-8")
                case _:
                    callable_node = None
                    callable_name = None
                    callable_kind = None
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
                    return_ty=return_ty,
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

        sorted_method_likes = sorted(method_likes, key=lambda x: x.start_byte)
        return sorted_method_likes

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

        sorted_enums = sorted(enums, key=lambda x: x.start_byte)
        return sorted_enums

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

        sorted_structs = sorted(structs, key=lambda x: x.start_byte)
        return sorted_structs

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
        interfaces_query_str = """
        (interface_declaration
          (modifier)* @interface_modifier
          name: (identifier) @interface_name
          (type_parameter_list)? @type_params
          (base_list)? @constraining_interfaces
          (type_parameter_constraints_clause)? @constraints) @interface_def
        """.strip()
        query = self.tree_sitter_lang.query(interfaces_query_str)
        matches = query.matches(self.tree.root_node)
        interfaces = []

        for _pat_idx, captures_by_name in matches:
            interface_node = captures_by_name["interface_def"][0]
            interface_name = captures_by_name["interface_name"][0].text.decode("utf-8")

            modifier_list = []
            if captures_by_name.get("interface_modifier"):
                for m in captures_by_name["interface_modifier"]:
                    modifier = CSharpInterfaceModifier.from_str(m.text.decode("utf-8"))
                    if modifier:
                        modifier_list.append(modifier)

            # TODO: Implement matching of generic type constraints to generic types
            type_params = []
            if captures_by_name.get("type_params"):
                for child in captures_by_name["type_params"][0].children:
                    if child.type in {
                        "type_parameter",
                    }:
                        type_params.append(child.text.decode("utf-8"))

            constraining_implementations = []
            if captures_by_name.get("constraining_interfaces"):
                for child in captures_by_name["constraining_interfaces"][0].children:
                    # TODO: Think about this -- needs to match what is extracted for
                    # TODO: `interface`s to make links (e.g., Interface or Interface<T>)
                    # TODO: Unify with solution in extracting interfaces.
                    if child.type in {
                        "identifier",
                        "qualified_name",
                        "generic_name",
                        "invocation_expression",
                    }:
                        constraining_implementations.append(child.text.decode("utf-8"))

            if interface_node and interface_name:
                start_line, end_line = self.get_node_line_range(interface_node)
                start_byte, end_byte = (
                    interface_node.start_byte,
                    interface_node.end_byte,
                )
                symbol_code = cs_node_to_text(self.source_bytes, interface_node)
                fully_qualified_parent_path = self._get_fully_qualified_path_to_parent(
                    node=interface_node
                )
                delimiter = "."
                bespoke_data = CSharpInterfaceData(
                    base_names=constraining_implementations,
                    modifiers=modifier_list,
                    type_params=type_params,
                )
                interface = RawTreeSitterSymbolData(
                    name=interface_name,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_kind=SymbolKind.INTERFACE,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    file_path=self.file_path,
                    fully_qualified_path_to_parent=fully_qualified_parent_path,
                    # TODO: unify interface base names with class/struct/enum
                    base_class_names=None,
                    symbol_code=symbol_code,
                    delimiter=delimiter,
                    bespoke_data=bespoke_data,
                )
                interfaces.append(interface)
            else:
                print(
                    f"Missing class name ({interface_name}) or node ({interface_node})"
                )

        sorted_interfaces = sorted(interfaces, key=lambda x: x.start_byte)
        return sorted_interfaces
