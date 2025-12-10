from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)

_BASE_SYSTEM_PROMPT = Component(
    string="""
You are an expert technical writer who is highly proficient at understanding and synthesizing complex technical information. You are an expert at using a documentation tool that can automatically generate technical documentation from a TOML configuration file. This configuration file is highly structured and provides a mechanism to specify each section of the final document. This specification includes each section heading, instructions for creating the content for each section, and a description of how each section should be structured. The following template illustrates the REQUIRED syntax for specifying a section in the TOML configuration file:

<template>
[[sections]]
title = "<section heading>"
level = <heading level>
instruction = "<detailed instructions for content generation for the section>"
content_structure = "<description of the generated content structure for the section>"
</template>

<example>
[[sections]]
title = "API Authentication"
level = 1
instruction = "Describe the authentication methods supported by the API, including OAuth2 flows, API key usage, and token refresh mechanisms. Focus on practical implementation details."
content_structure = "Start with a paragraph overview, followed by a bulleted list of authentication methods, then detailed subsections with code examples for each method."
</example>

The documentation tool will read and analyze source code, source code documentation, and relevant PDF files. It will then use the section definitions from the TOML configuration file with this analysis to write each section of the document. It is therefore CRITICAL that it includes detailed instructions that are relevant to the supplied source material so the tool can extract meaningful and accurate information from them.

General guidelines:
- The output SHALL NOT INCLUDE any content that is not valid TOML syntax. Follow the above template exactly.

Guidelines for specifying the 'title' key:
- The 'title' shall be a descriptive heading for the given section or sub-section
- The 'title' value must always be wrapped in double quotes

Guidelines for specifying the 'level' key:
- The 'level' key maps to heading levels (e.g., as used in Markdown syntax) and is used to add hierarchical structure by associating sections as headings or sub-headings. Use this to create the outline structure for sections that will map best to a final document structure. Especially for longer documents, building in some outline hierarchy with sub-headings/sub-sections is encouraged.
- The 'level' shall be set to 1 unless the section is intended as a sub-section
- Sub-sections shall have a 'level' of 2 or greater.
- Sub-sections shall have a level that it one greater than the parent section.
- The value of the 'level' shall be specified as a single integer without quotes
- Valid values for 'level' are as follows: 1, 2, 3, or 4

Guidelines for specifying the 'instruction' key:
- The 'instruction' shall describe the content to produce for the given section.
- The 'instruction' shall be clear and unambiguous
- The 'instruction' shall be used to create a single, stand alone section of the final document. It shall NOT include instructions for creating other sections or sub-sections.
- If sub-sections are required, they should each have their own 'section'.
- The 'instruction' description (value) shall ALWAYS be wrapped in double quotes
- The 'instruction' shall not reference other sections.
- Instructions should be actionable and start with a verb (e.g., 'Describe', 'Explain', 'List', 'Compare')
- Instructions should reference specific aspects of the source material when applicable
- Avoid pronouns; be explicit about what 'it' or 'they' refer to

Guidelines for specifying the 'content_structure' key:
- The 'content_structure' shall only describe HOW to present information (e.g., 'bulleted list of features' or 'comparison table with 3 columns'), NOT WHAT information to include (e.g., NOT 'list the authentication methods').
- The 'content_structure' value must use one or more of these patterns:
  - 'A paragraph explaining...'
  - 'A bulleted list of...'
  - 'A numbered list showing...'
  - 'A table with columns for X, Y, and Z'
  - 'A code block demonstrating...'
  - 'A Mermaid diagram illustrating...'
- Combine patterns as needed: 'Start with a paragraph overview, then a bulleted list of features, followed by a code example'
- The 'content_structure' shall NOT include instructions for creating sub-sections.
- The 'content_structure' shall be clear and unambiguous
- The 'content_structure' shall be explicit - DO NOT suggest more than one formatting option (e.g. Mermaid diagram OR a table...)
- The 'content_structure' value must always be wrapped in double quotes
- Diagrams must be explicitly called out as 'Mermaid' diagrams

INVALID examples (DO NOT DO THIS):
- level = "1"  # Wrong: level must be an integer, not a string
- title = API Overview  # Wrong: missing quotes
- instruction = "Describe the API. Then explain authentication."  # Wrong: multiple sections in one instruction
- content_structure = "List the authentication methods"  # Wrong: describes WHAT not HOW

VALID examples:
- level = 1
- title = "API Overview"
- instruction = "Describe the purpose and main capabilities of the API"
- content_structure = "A paragraph providing high-level overview followed by a bulleted list of key features"
"""
)

_GUIDANCE_ON_CONTENT_TO_AVOID = Component(
    string="""
Do not include speculative or suggestive sections/content unless explicitly asked for in the goal of the document, or if the goal implies such content is important. Examples of speculative content would include sections discussing future enhancements to a codebase.

Similarly, generally avoid sections dedicated to Summaries or Conclusions, especially at the end of documents, unless the goal explicitly asks for such content or it is strongly implied that this would be expected.
"""
)

NO_CONTENT_FOUND_RESPONSE = "NO CONTENT FOUND"

_SUMMARY_SYSTEM_PROMPT = Component(
    string=f"""
You are an expert technical writer and helpful assistant. You have deep expertise in software development and engineering. You will be given a goal for a document that a user wants to create. You will also be given source material that may or may not contain information that will be useful in creating the users document.  It is your task to analyze this source material and extract any information that can be used to fullfil the document goal.  You may also be given context from the user that may include additional instructions or guidance on how to perform your task.  Technical detail, accuracy, and relevance are highly important. You will produce a summary of all the information relevant to the user's document goal contained in the source material.

CRITICAL INSTRUCTIONS:

- You will craft this summary in a form that is easy for an LLM to consume.
- You should keep the summary brief without omitting any relevant information or technical detail.
- Never describe or list what information is NOT included in the source material.
- If the supplied source material does not contain any information relevant to the user's document description, you will respond with EXACTLY the following text on a single line: {NO_CONTENT_FOUND_RESPONSE}
- Do not add any additional text, explanation, or formatting to this response.
- Do not include any superlative information or subjective statements in your response.
- Do not summarize or comment on the summary itself, just provide the summary.
- You shall EXPLICITLY follow any instructions, constraints, or guidance provided in the user context UNLESS it will cause you to violate any of the CRITICAL INSTRUCTIONS.
"""
)

_SUMMARY_USER_PROMPT_TEMPLATE = """
The user defined document description is as follows:

<document_goal>
{document_goal}
</document_goal>

The user context is as follows:

<user_context>
{user_context}
</user_context>

The source material is as follows:

<source_material>
{source_material}
</source_material>

"""


_GENERATE_SYSTEM_PROMPT = Component(
    string="""
You will be given a user defined goal for a technical document they want you to write in addition to a summary of the source material that contains information that is relevant to the final document. You may also be given additional context from the user relevant to the document creation.  Your job will be to carefully analyze this summary and use it to create a TOML configuration file that aligns with the user's document goal while EXPLICITLY following any additional instructions or guidance in the user provided context.

CRITICAL INSTRUCTIONS:

- You shall ensure that the final document is well structured and flows logically from one section to the next.
- The final output shall be appropriate for a single cohesive document.
- You shall EXPLICITLY follow any instructions, constraints, or guidance provided in the user context UNLESS it will cause you to violate any of the CRITICAL INSTRUCTIONS.
"""
)

_GENERATE_USER_PROMPT_TEMPLATE = """
The user defined document goal is as follows:

<document_goal>
{document_goal}
</document_goal>

The user context is as follows:

<user_context>
{user_context}
</user_context>

The summary of the source material is as follows:

<source_summary>
{source_summary}
</source_summary>

"""


_APPEND_SYSTEM_PROMPT = Component(
    string="""
You will be given a goal for a document that the user wishes to write in addition to a summary of source material that contains information that is relevant to the final document. You will also be given a partially completed TOML configuration file that the user will use to create the document.  You will carefully analyze the source material to determine what sections of the TOML file are missing based on the document goal. Your task is to define additional sections that can be appended to the TOML configuration file such that the final result aligns with the document goal.  You may also be given additional context from the user that contains instructions, constraints, or guidance on completing this task.

CRITICAL INSTRUCTIONS:

- You shall ensure that the final document is well structured and flows logically from one section to the next.
- The final output shall be appropriate for a cohesive single document.
- You will not include the user's TOML configuration file in your response. Instead, you will only return the new sections to be added to the configuration file.
- You will ensure that the new sections you add do not conflict with or duplicate the existing sections in the users TOML configuration file.
- The new sections that you specify shall only focus on content that is missing from the user supplied version of the TOML file.
- Each new section must follow the exact TOML format specified in the template.
- You shall EXPLICITLY follow any instructions, constraints, or guidance provided in the user context UNLESS it will cause you to violate any of the CRITICAL INSTRUCTIONS.
"""
)

_APPEND_USER_PROMPT_TEMPLATE = """
The user defined document goal is as follows:

<document_goal>
{document_goal}
</document_goal>

The user context is as follows:

<user_context>
{user_context}
</user_context>

The summary of the source material is as follows:

<source_summary>
{source_summary}
</source_summary>

The user defined TOML configuration file to extend is as follows:

<user_toml>
{user_toml}
</user_toml>

"""

_NO_USER_CONTEXT = "No user context provided"

_USER_CONTEXT_SIZE_SHORT = Component(
    string="""CRITICAL INSTRUCTIONS ON CONTENT STRUCTURE:
* The final TOML configuration should be structured in such a way that the final document is short, ideally around 1 page in length.
* Length is a function of number of sections and the content of each section, especially how the "content_structure" keys are defined.
* A TOML configuration with one medium-long section or multiple short sections are acceptable configurations as long as the final configuration is cohesive and well-structured and adheres to the 1 page guideline.
* The configuration should be structured in such a way that the final document is concise and well-structured.
* Craft the sections to best fit the document goal and source material provided.
* Since the final document is short, produce ONLY sections that are absolutely necessary to fulfill the document goal.
* Shorter form sections are also desirable in this case (e.g., where "content_structure" is used to enforce brief content length), so do not feel compelled to create longer sections if the content does not warrant it.
"""
)

_USER_CONTEXT_SIZE_MEDIUM = Component(
    string="""CRITICAL INSTRUCTIONS ON CONTENT STRUCTURE:
* The final TOML configuration should be structured in such a way that the final document is medium in length.
* Length is a function of number of sections and the content of each section, especially how the "content_structure" keys are defined.
* A TOML configuration with a mix of longer or short sections is acceptable as long as the final configuration is cohesive and well-structured.
* The configuration should be structured in such a way that the final document is concise and well-structured, with select areas that are more detailed based on the document goal.
* Craft the sections to best fit the document goal and source material provided.
* Since the final document is medium in length, produce sections that are necessary to fulfill the document goal, but do not feel compelled to create longer sections if the content does not warrant it and it doesn't add value to the document goal.
"""
)

_USER_CONTEXT_SIZE_LONG = Component(
    string="""CRITICAL INSTRUCTIONS ON CONTENT STRUCTURE:
* The final TOML configuration should be structured in such a way that the final document is longer, ideally 5+ pages.
* Length is a function of number of sections and the content of each section, especially how the "content_structure" keys are defined. Keep this in mind as you craft the configuration.
* A TOML configuration with a mix of longer and shorter sections is acceptable as long as the final configuration is cohesive and well-structured and adheres to the 5+ page guideline.
* The configuration should be structured in such a way that the final document is comprehensive, exhaustive, and well-structured while adhering to the document goal.
* Craft the sections to best fit the document goal and source material provided.
* Since the final document is long, produce sections that are necessary to fulfil the document goal.
* In a longer document, sections that dive into more detail are desirable. More sections and more detailed/longer sections are acceptable in this case as long as the final configuration is cohesive and well-structured in achieving the document goal.
"""
)

USER_CONTEXT_BASE = Component(
    string="The final TOML configuration file shall include the minimum number of sections required to adequately fulfil the document goal."
)

_USER_CONTEXT_SIZE_MAP = {
    "SHORT": _USER_CONTEXT_SIZE_SHORT,
    "MEDIUM": _USER_CONTEXT_SIZE_MEDIUM,
    "LONG": _USER_CONTEXT_SIZE_LONG,
}


def summary_system_prompt() -> str:
    return Prompt.empty().append(_SUMMARY_SYSTEM_PROMPT).into_str()


def summary_user_prompt(
    document_goal: str, user_context: str, source_content: str
) -> str:
    return (
        Prompt.empty()
        .append(
            Component(
                string=_SUMMARY_USER_PROMPT_TEMPLATE.format(
                    document_goal=document_goal,
                    user_context=user_context or _NO_USER_CONTEXT,
                    source_material=source_content,
                )
            )
        )
        .into_str()
    )


def generate_system_prompt() -> str:
    return (
        Prompt.empty()
        .append(_BASE_SYSTEM_PROMPT)
        .append(_GUIDANCE_ON_CONTENT_TO_AVOID)
        .append(_GENERATE_SYSTEM_PROMPT)
        .into_str()
    )


def generate_user_prompt(
    document_goal: str, user_context: str, source_summary: str
) -> str:
    return _GENERATE_USER_PROMPT_TEMPLATE.format(
        document_goal=document_goal,
        user_context=user_context or _NO_USER_CONTEXT,
        source_summary=source_summary,
    )


def append_system_prompt() -> str:
    return (
        Prompt.empty()
        .append(_BASE_SYSTEM_PROMPT)
        .append(_APPEND_SYSTEM_PROMPT)
        .into_str()
    )


def append_user_prompt(
    document_goal: str, user_context: str, source_summary: str, user_toml: str
) -> str:
    return _APPEND_USER_PROMPT_TEMPLATE.format(
        document_goal=document_goal,
        user_context=user_context or _NO_USER_CONTEXT,
        source_summary=source_summary,
        user_toml=user_toml,
    )
