import string
from typing import Any, Self

from pydantic import BaseModel


class ResolvedComponent(BaseModel):
    string: str

    def __str__(self) -> str:
        return self.string

    def __add__(self, other: Self) -> Self:
        return ResolvedComponent(string=self.string + other.string)


class RawPromptComponent(BaseModel):
    string: str
    format_fields: set[str]

    @classmethod
    def from_raw_str(cls, raw_str: str) -> Self:
        return cls(string=raw_str, format_fields=set())

    @classmethod
    def from_templated_str(cls, templated_str: str) -> Self:
        formatter = string.Formatter()
        format_fields = set()

        # Only support simple identifiers
        for _literal_text, field_name, _format_spec, _conversion in formatter.parse(
            templated_str
        ):
            if field_name is not None:
                format_fields.add(field_name)

        return cls(string=templated_str, format_fields=format_fields)

    def resolve(self, format_args: dict[str, Any] | None = None) -> ResolvedComponent:
        if format_args is None and self.format_fields:
            raise ValueError(
                "Expected format args: {self.format_fields}, got `None` supplied"
            )
        if format_args and self.format_fields != set(format_args.keys()):
            raise ValueError(
                f"Supplied format args: {set(format_args.keys())} != expected set: {self.format_fields}"
            )

        return (
            ResolvedComponent(string=self.string.format(**format_args).strip())
            if format_args
            else ResolvedComponent(string=self.string.strip())
        )


class Prompt(BaseModel):
    components: list[ResolvedComponent]

    @classmethod
    def empty(cls) -> Self:
        return cls(components=[])

    def append(self, component: ResolvedComponent) -> Self:
        self.components.append(component)
        return self

    def extend(self, other: Self) -> Self:
        self.components.extend(other.components)
        return self

    def prepend(self, component: ResolvedComponent) -> Self:
        self.components.insert(index=0, object=component)
        return self

    def into_str(self, sep: str = "") -> str:
        return sep.join([str(c) for c in self.components])

    def __add__(self, other: Self) -> Self:
        return Prompt(components=self.components + other.components)


GENERAL_STE_STYLE_INSTRUCTION = Prompt(
    components=[
        RawPromptComponent.from_raw_str(
            raw_str="""
In the content that you provide, you **must adhere** to the following style and copy editing instructions:

- Make sure content conforms to ASD-STE100 Simplified Technical English (STE).
- Do not comment on the subjective qualities of content. For example, do not use language like "robust", "comprehensive and modular",  or other superluous descriptions, adjectives, and modifiers. This is irrelevant to your goals of documenting technical content.
- Do not use speculative language such as "this is likely ..." or "probably."
- **Focus** on directly communicating the technical details in simple English.
"""
        ).resolve()
    ]
)


NO_RESTATEMENT_STYLE_INSTRUCTION = Prompt(
    components=[
        RawPromptComponent.from_raw_str(
            raw_str="""
In your output do not restate the identify of the component you are documenting technically.

For example, do not do the following:
- "The <name> codebase provides ..."
- "The <file> in the <codebae_name> codebase provies ..."
- "The <folder> in the <codebase_name> contains ..."

Instead, you would do the following:
- "Provides ..."
- "Provides ..."
- "Contains ..."
"""
        ).resolve()
    ]
)


TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION = Prompt(
    components=[
        RawPromptComponent.from_raw_str(
            raw_str="""
Your output is just one extremely terse single sentence. It is intended to fit on a single line in various media, therefore it must be no longer than 100 characters.
"""
        ).resolve()
    ]
)
