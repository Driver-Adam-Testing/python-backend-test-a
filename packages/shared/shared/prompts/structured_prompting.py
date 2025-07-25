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
- "The <method_name> method transforms/provides/implements ..."
- "The <function_name> function processes... "
- "The <class_name> class represents ..."

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


DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB = Component(
    string="""This will be part of technical documentation. At the start of your output, identify the kind or category of thing you are describing followed by an action verb or more broadly the content that is relevant. Here is an example for if you are asked to document something about a whole codebase. The concept of more information dense description applies to other things you may be asked to document: For example, if you are describing a codebase as a whole that is clearly a library, you would start with something like "A library that implements ..." or if it is clearly a web application, then you would start with something like "A web application for ...". The key point is to **not** just state that it is a codebase or repo (e.g., not start with "A codebase that ..."), but to provide more information immediately by stating what **kind** of code.
    """
)


NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE = Component(
    string="""This will be part of technical documentation for the source metadata content. In your output, do not refer to the fact that this content was provided to you in any way. For example, **do not** start off with something like "The provided configuration file..." Just start explaining the purpose of the content directly as you would find in typical, high quality technical documentation. So you might start out with "This configuration file ..." or even better, no reference to "this configuration file" is needed so you immediately start describing the purpose/functionality. As another example, prefer language like "This configuration file sets ..." instead of "The configuration file sets ..." which is more natural for documentation explicitly associated with a particular file, which is what you are building.
"""
)

USE_BACKTICKS_STYLE_INSTRUCTION = Component(
    string="""In your output, **make sure** to enclose any references to source code contents or symbols in single backticks. E.g.: "In the `MyClass` class ..." (not "In the MyClass class ..." or "In the 'MyClass' class ..." etc.)
    """
)

USE_TRIPLE_BACKTICS_FOR_CODE_BLOCKS_STYLE_INSTRUCTION = Component(
    string="""In your output, **make sure** to enclose any code blocks in triple backticks. Also, annotate the code block with the language identifier for the language of the code, according to the Markdown fenced code blocks syntax. E.g.: ```<language>\n<large code block here```. **Do not** however enclose the general Markdown prose of your output (Markdown is the standard syntax for non-code block language prose) inside of code fences.
"""
)

RETURN_UNEDITED_CONTENT_IF_NO_SUBSTANTIAL_CHANGES_FOLDERS = Component(
    string="""Below is the content generated for this folder for the previous version. If the content still applies as is, return it unchanged. Otherwise, return an updated version of the content that reflects any changes in the folder structure or contents. If there are no changes, you can return the content as is without any modifications.
    """
)

GENERIC_MARKDOWN_OUTPUT_INSTRUCTION = Component(
    string="""
Make sure you format your output in Markdown format using, as relevant, Markdown syntax for headings, list, etc. and enclosing single code references with single backticks and large complete code blocks in triple backticks.
    """
)

NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING = Component(
    string="""
Do not use special formatting, such as backticks or other forms of Markdown syntax, in your text output. Your output is to be consumed as raw text, so special formatting cannot be rendered correctly.
    """
)
