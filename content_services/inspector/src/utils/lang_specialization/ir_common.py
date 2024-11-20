from __future__ import annotations

import abc
from typing import Self

import openai
from pydantic import BaseModel, PrivateAttr
from utils.lang_specialization.symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ScopeRelation,
)
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind


def snake_case_to_spaced_string(snake_case: str) -> str:
    split_str = snake_case.split("_")
    return " ".join(item.capitalize() for item in split_str)


class MdRenderable(BaseModel, abc.ABC):
    @abc.abstractmethod
    def render_markdown(self, doc_label: str) -> str:
        pass


class RawContent(MdRenderable):
    content: str

    def render_markdown(self, doc_label: str) -> str:
        return f"{self.content}\n"


class FieldNameWithBackTickContent(MdRenderable):
    content: str

    def render_markdown(self, doc_label: str) -> str:
        return f"- **{snake_case_to_spaced_string(doc_label)}**: `{self.content}`\n"


class FieldNameWithBulletedContent(MdRenderable):
    content: str

    def render_markdown(self, doc_label: str) -> str:
        return (
            f"- **{snake_case_to_spaced_string(doc_label)}**:\n    - {self.content}\n"
        )


class FieldNameWithRawContent(MdRenderable):
    content: str

    def render_markdown(self, doc_label: str) -> str:
        return f"- **{snake_case_to_spaced_string(doc_label)}**: {self.content}\n"


class NamedContent(MdRenderable):
    name: str
    content: str

    def render_markdown(self, doc_label: str) -> str:
        return f"    - `{self.name}`: {self.content}\n"


class ListedBacktickNameRawContentNoNone(MdRenderable):
    content: list[NamedContent]

    def render_markdown(self, doc_label: str) -> str:
        output_str = ""
        if len(self.content) > 0:
            output_str += f"- **{snake_case_to_spaced_string(doc_label)}**:\n"
            for item in self.content:
                output_str += item.render_markdown(doc_label)
        return output_str


class ListedBacktickNameRawContentWithNone(MdRenderable):
    content: list[NamedContent]

    def render_markdown(self, doc_label: str) -> str:
        output_str = ""
        output_str += f"- **{snake_case_to_spaced_string(doc_label)}**:\n"
        if len(self.content) > 0:
            for item in self.content:
                output_str += item.render_markdown(doc_label)
        else:
            output_str += "    - None\n"
        return output_str


class ListedRawContentNoNone(MdRenderable):
    content: list[str]

    def render_markdown(self, doc_label: str) -> str:
        output_str = ""
        if len(self.content) > 0:
            output_str += f"- **{snake_case_to_spaced_string(doc_label)}**:\n"
            for item in self.content:
                output_str += f"    - {item}\n"
        return output_str


class ListedRawContentWithNone(MdRenderable):
    content: list[str]

    def render_markdown(self, doc_label: str) -> str:
        output_str = ""
        output_str += f"- **{snake_case_to_spaced_string(doc_label)}**:\n"
        if len(self.content) > 0:
            for item in self.content:
                output_str += f"    - {item}\n"
        else:
            output_str += "    - None\n"
        return output_str


class ListData(BaseModel):
    data: list[str]

    @classmethod
    def from_llm(
        cls, llm: ChatOpenAI, system_prompt: str, user_prompt: str, code: str
    ) -> Self:
        user_prompt_complete = f"{user_prompt}\n\nCode:\n\n{code}"
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)

    def render_markdown(self) -> str:
        output = ""
        output += "\n---\n"
        for dep in self.data:
            output += f"- `{dep}`\n"
        output += "\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class IrData(BaseModel, abc.ABC):
    _children: list = PrivateAttr(default_factory=list)
    _supported_child_ordering: list[ScopeRelation] = PrivateAttr(
        default=[]
    )  # provide a list of field names in the order they should be rendered
    # Support for children and how they are presented are now defined by _supported_child_ordering and
    # _child_to_ir and _child_to_field_name, rather than as explicit fields here.

    @classmethod
    @abc.abstractmethod
    def system_prompt(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        # when constructing this method - if you have a field that you just want listed with no
        # additional IR content needed, return None from this function when that type of symbol is passed
        # e.g. nested classes that are just listed
        pass

    @classmethod
    @abc.abstractmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def default_instance(cls) -> Self:
        pass

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        symbol: RawSymbolData,
    ) -> Self:
        if symbol.symbol_code is None:
            # handle C++ classes defined in header
            cls_instance = cls.default_instance()
        else:
            try:
                content_raw = llm.generate_response(
                    system_prompt=cls.system_prompt(),
                    user_prompt=cls.user_prompt(symbol),
                    output_cfg=OutputConfig(
                        kind=OutputConfigKind.JSON_STRICT, payload=cls
                    ),
                )
            except openai.LengthFinishReasonError as _:
                print("LengthFinishReasonError caught")
                return None
                # TODO: do something with this - switch to default_instance
            cls_instance = cls.parse_raw(content_raw)

        for child_symbol in symbol.children:
            child_ir_cls = cls.child_to_ir(child_symbol)
            child_content = (
                child_ir_cls.from_llm(llm, child_symbol) if child_ir_cls else None
            )

            cls_instance._children.append((child_symbol, child_content))

        return cls_instance

    def render_markdown(self) -> str:
        output = ""

        # doesn't handle children, since children is a private attribute
        for label_name, label_content in self:
            if isinstance(label_content, MdRenderable):
                output += label_content.render_markdown(label_name)
            else:
                raise ValueError(
                    f"Unsupported field content type for {label_name}: {type(label_content)}. Add a MdRenderable class to render this content."
                )

        # Render child data
        child_dictionary = {
            label_name: "" for label_name in self._supported_child_ordering
        }
        for child_symbol, child_content in self._children:
            label_name = self.child_to_field_name(child_symbol)
            if len(child_dictionary[label_name]) == 0:
                child_dictionary[label_name] += f"\n**{label_name}**\n"

            if label_name not in child_dictionary:
                raise ValueError(f"Unsupported child field name: {label_name}")

            if child_content is not None:
                scoped_name = (
                    child_symbol.scope.split(child_symbol.delimiter)[-1]
                    + child_symbol.delimiter
                    + child_symbol.name
                    if child_symbol.scope
                    else child_symbol.name
                )
                child_dictionary[label_name] += f"\n---\n#### {scoped_name}\n"
                child_dictionary[label_name] += child_content.render_markdown()
            else:
                child_dictionary[label_name] += f"    - {child_symbol.name}\n"

        for _, label_content in child_dictionary.items():
            output += label_content

        output += "\n"
        return output


class IrCollection(BaseModel, abc.ABC):
    data: dict[str, IrData | list[IrData]]

    @classmethod
    def from_llm_with_ir_data(
        cls,
        ir_data: type[IrData],
        llm: ChatOpenAI,
        symbols_list: RawSymbolCollection,
    ) -> Self:
        symbols_dict = {}
        for _, s in symbols_list.data.items():
            if isinstance(s, list):
                for item in s:
                    if item.name not in symbols_dict:
                        symbols_dict[item.name] = []
                    symbols_dict[item.name].append(
                        ir_data.from_llm(
                            llm=llm,
                            symbol=item,
                        )
                    )
            elif isinstance(s, RawSymbolData):
                if s.name not in symbols_dict:
                    symbols_dict[s.name] = []
                symbols_dict[s.name].append(
                    ir_data.from_llm(
                        llm=llm,
                        symbol=s,
                    )
                )
        return cls(data=symbols_dict)

    @classmethod
    @abc.abstractmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        symbols_list: RawSymbolCollection,
    ) -> Self:
        pass

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            for item in v:
                output += f"\n---\n### {k}\n"
                output += item.render_markdown()

        return output

    def __str__(self) -> str:
        return self.render_markdown()


### Default Classes, must still be inherited from, or create new ones for any specialization ###
class VariableData(IrData):
    type: FieldNameWithBackTickContent
    description: FieldNameWithRawContent
    use: FieldNameWithRawContent

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            type="",
            description="",
            use="",
        )


class DataStructureData(IrData, abc.ABC):
    type: FieldNameWithBackTickContent
    members: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            type="",
            members=[],
            description="",
        )


class FnData(IrData, abc.ABC):
    single_sentence: RawContent
    inputs: ListedBacktickNameRawContentWithNone
    control_flow: ListedRawContentWithNone
    output: FieldNameWithBulletedContent

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            single_sentence="",
            inputs=[],
            control_flow=[],
            output="",
        )


class ClassData(IrData, abc.ABC):
    type: FieldNameWithBackTickContent
    members: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent
    inherits_from: ListedRawContentNoNone
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[ScopeRelation.METHOD, ScopeRelation.NESTED_CLASS]
    )

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            description="Implemented elsewhere",
            type="",
            members=[],
            inherits_from=[],
        )
