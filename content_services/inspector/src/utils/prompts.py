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

Here are some examples to understand what is meant. These are just examples, you do not need to use the particular words here unless it is relevant to how you would describe the content.
- "The <name> codebase provides ..."
- "The <file> in the <codebase_name> codebase implements X, Y, Z data structures ..."
- "The <folder> in the <codebase_name> contains tools for ..."

Instead, you should be more direct such as providing just:
- "Provides ..."
- "Implements X, Y, Z data structures ..."
- "Tools for ..."
"""
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS = Component(
    string="""
In your output do not restate the identify of the component you are documenting technically.

Here are some examples to understand what is meant. These are just examples, you do not need to use the particular words here unless it is relevant to how you would describe the content.
- "The `<method_name>` method transforms/provides/implements ..."
- "The `<function_name>` function processes... "
- "The `<class_name>` class represents ..."

Instead, you should be more direct such as providing just:
- "Transforms/provides/implements ..."
- "Processes ..."
- "Represents ..."
"""
)


TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION = Component(
    string="""
Your output is just one extremely terse single sentence. It is intended to fit on a single line in various media, therefore it must be no longer than 100 characters.
"""
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE = Component(
    string="""This will be part of technical documentation for the source code. In your output, do not refer to the fact that this code was provided to you in any way. For example, **do not** start off with something like "The provided module..." Just start explaining the purpose of the code directly as you would find in typical, high quality technical documentation for the relevant language. So you might start out with "This module ..." or even better, no reference to "this module" is needed so you immediately start describing the purpose/functionality. As another example, prefer language like "This code is a test suite for ..." instead of "The code is a test suite for ..." which is more natural for documentation explicitly associated with a particular file, which is what you are building.
"""
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE = Component(
    string="""This will be part of technical documentation for the source metadata content. In your output, do not refer to the fact that this content was provided to you in any way. For example, **do not** start off with something like "The provided configuration file..." Just start explaining the purpose of the content directly as you would find in typical, high quality technical documentation. So you might start out with "This configuration file ..." or even better, no reference to "this configuration file" is needed so you immediately start describing the purpose/functionality. As another example, prefer language like "This configuration file sets ..." instead of "The configuration file sets ..." which is more natural for documentation explicitly associated with a particular file, which is what you are building.
"""
)
