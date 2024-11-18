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


class RawContent(BaseModel):
    # Rendered as f"{content}\n"
    content: str

    def render_markdown(self, field_name: str) -> str:
        return f"{self.content}\n"


class FieldNameWithBackTickContent(BaseModel):
    # Rendered as f"**{snake_case_to_spaced_string(field_name)}**: `{content}`\n"
    content: str

    def render_markdown(self, field_name: str) -> str:
        return f"- **{snake_case_to_spaced_string(field_name)}**: `{self.content}`\n"


class FieldNameWithBulletedContent(BaseModel):
    # Rendered as f"**{snake_case_to_spaced_string(field_name)}**:\n    - {content}\n"
    content: str

    def render_markdown(self, field_name: str) -> str:
        return (
            f"- **{snake_case_to_spaced_string(field_name)}**:\n    - {self.content}\n"
        )


class FieldNameWithRawContent(BaseModel):
    # Rendered as f"**{snake_case_to_spaced_string(field_name)}**: {content}\n"
    content: str

    def render_markdown(self, field_name: str) -> str:
        return f"- **{snake_case_to_spaced_string(field_name)}**: {self.content}\n"


class NamedContent(BaseModel):
    # Only to be used in a list, rendered as:
    # f"**{snake_case_to_spaced_string(field_name)}**:\n `{name}`: {content}\n ..."
    name: str
    content: str

    def render_markdown(self, field_name: str) -> str:
        return f"    - `{self.name}`: {self.content}\n"


class ListedBacktickNameRawContentNoNone(BaseModel):
    # Rendered as:
    # f"**{snake_case_to_spaced_string(field_name)}**: \n - `{name}`: {content}\n
    # for each NamedContent in the list. If no entries in list, no content is produced
    content: list[NamedContent]

    def render_markdown(self, field_name: str) -> str:
        output_str = ""
        if len(self.content) > 0:
            output_str += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
            for item in self.content:
                output_str += item.render_markdown(field_name)
        return output_str


class ListedBacktickNameRawContentWithNone(BaseModel):
    # Rendered as:
    # f"**{snake_case_to_spaced_string(field_name)}**: \n - `{name}`: {content}\n
    # for each NamedContent in the list. If no entries in list, list is simply - None
    content: list[NamedContent]

    def render_markdown(self, field_name: str) -> str:
        output_str = ""
        output_str += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
        if len(self.content) > 0:
            for item in self.content:
                output_str += item.render_markdown(field_name)
        else:
            output_str += "    - None\n"
        return output_str


class ListedRawContentNoNone(BaseModel):
    # Rendered as:
    # f"**{snake_case_to_spaced_string(field_name)}**: \n - {content}\n
    # for each str in the list. If no entries in list, no heading is rendered
    content: list[str]

    def render_markdown(self, field_name: str) -> str:
        output_str = ""
        if len(self.content) > 0:
            output_str += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
            for item in self.content:
                output_str += f"    - {item}\n"
        return output_str


class ListedRawContentWithNone(BaseModel):
    # Rendered as:
    # f"**{snake_case_to_spaced_string(field_name)}**: \n - {content}\n
    # for each str in the list. If no entries in list, no heading is rendered
    content: list[str]

    def render_markdown(self, field_name: str) -> str:
        output_str = ""
        output_str += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
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
        for field_name, field_content in self:
            if isinstance(
                field_content,
                RawContent
                | FieldNameWithBackTickContent
                | FieldNameWithBulletedContent
                | FieldNameWithRawContent
                | ListedBacktickNameRawContentNoNone
                | ListedBacktickNameRawContentWithNone
                | ListedRawContentNoNone
                | ListedRawContentWithNone,
            ):
                output += field_content.render_markdown(field_name)
            elif isinstance(field_content, str):
                if len(field_content) > 0:
                    output += f"- **{snake_case_to_spaced_string(field_name)}**: {field_content}\n"
            elif isinstance(field_content, list):
                if len(field_content) > 0:
                    output += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
                    for item in field_content:
                        if isinstance(item, str):
                            output += f"    - {item}\n"
                        elif isinstance(item, NamedContent):
                            output += item.render_markdown(field_name)
                        else:
                            raise ValueError(
                                f"Unsupported item type in list: {type(item)}"
                            )
            else:
                raise ValueError(
                    f"Unsupported field content type for {field_name}: {type(field_content)}"
                )

        # Render child data
        child_dictionary = {
            field_name: "" for field_name in self._supported_child_ordering
        }
        for child_symbol, child_content in self._children:
            field_name = self.child_to_field_name(child_symbol)
            if len(child_dictionary[field_name]) == 0:
                child_dictionary[field_name] += f"\n**{field_name}**\n"

            if field_name not in child_dictionary:
                raise ValueError(f"Unsupported child field name: {field_name}")

            if child_content is not None:
                scoped_name = (
                    child_symbol.scope.split(child_symbol.delimiter)[-1]
                    + child_symbol.delimiter
                    + child_symbol.name
                    if child_symbol.scope
                    else child_symbol.name
                )
                child_dictionary[field_name] += f"\n---\n#### {scoped_name}\n"
                child_dictionary[field_name] += child_content.render_markdown()
            else:
                child_dictionary[field_name] += f"    - {child_symbol.name}\n"

        for _, field_content in child_dictionary.items():
            output += field_content

        output += "\n"
        return output


class IrCollection(BaseModel, abc.ABC):
    data: dict[str, IrData | list[IrData]]

    @classmethod
    def dict_from_llm(
        cls,
        data_cls: type[IrData],
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
                        data_cls.from_llm(
                            llm=llm,
                            symbol=item,
                        )
                    )
            elif isinstance(s, RawSymbolData):
                if s.name not in symbols_dict:
                    symbols_dict[s.name] = []
                symbols_dict[s.name].append(
                    data_cls.from_llm(
                        llm=llm,
                        symbol=s,
                    )
                )
        return cls(data=symbols_dict)

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
