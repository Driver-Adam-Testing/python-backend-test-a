from typing import Self

from pydantic import BaseModel, field_validator


class Component(BaseModel):
    string: str

    @field_validator("string")
    @classmethod
    def strip_string(cls, s: str) -> str:
        return s.strip()

    def __str__(self) -> str:
        return self.string

    def __add__(self, other: Self) -> Self:
        return Component(string=self.string + other.string)


class Prompt(BaseModel):
    components: list[Component]

    @classmethod
    def empty(cls) -> Self:
        return cls(components=[])

    def append(self, component: Component) -> Self:
        self.components.append(component)
        return self

    def extend(self, other: Self) -> Self:
        self.components.extend(other.components)
        return self

    def prepend(self, component: Component) -> Self:
        self.components.insert(index=0, object=component)
        return self

    def into_str(self, sep: str = "\n\n") -> str:
        return sep.join([str(c) for c in self.components])

    def __add__(self, other: Self) -> Self:
        return Prompt(components=self.components + other.components)


GENERAL_STE_STYLE_INSTRUCTION = Component(
    string="""
In the content that you provide, you **must adhere** to the following style and copy editing instructions:

- Make sure content conforms to ASD-STE100 Simplified Technical English (STE).
- Do not comment on the subjective qualities of content. For example, do not use language like "robust", "comprehensive and modular", or other superfluous descriptions, adjectives, and modifiers. This is irrelevant to your goals of documenting technical content.
- Do not use speculative language such as "this is likely ..." or "probably."
- **Focus** on directly communicating the technical details in simple English.
"""
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES = Component(
    string="""
In your output do not restate the identify of the component you are documenting technically.

For example, do not do the following:
- "The <name> codebase provides ..."
- "The <file> in the <codebase_name> codebase provies ..."
- "The <folder> in the <codebase_name> contains ..."

Instead, you would do the following:
- "Provides ..."
- "Provides ..."
- "Contains ..."
"""
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS = Component(
    string="""
In your output do not restate the identify of the component you are documenting technically.

For example, do not do the following:
- "The `<method_name>` method provides ..."
- "The `<function_name>` function waits... "
- "The `<class_name>` class represents ..."

Instead, you would do the following:
- "Provides ..."
- "Waits ..."
- "Represents ..."
"""
)


TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION = Component(
    string="""
Your output is just one extremely terse single sentence. It is intended to fit on a single line in various media, therefore it must be no longer than 100 characters.
"""
)
