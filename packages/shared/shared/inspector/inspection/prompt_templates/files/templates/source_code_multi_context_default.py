from shared.inspector.utils.lang_specialization.default import (
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    DefaultDataStructureCollection,
    DefaultDataStructureRawSymbolCollection,
    DefaultFnCollection,
    DefaultFnRawSymbolCollection,
    DefaultVariableCollection,
    DefaultVariableRawSymbolCollection,
)
from shared.inspector.utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from shared.inspector.utils.templates import S
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_PURPOSE_FROM_CHUNKS))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Global Variables",
        DefaultVariableRawSymbolCollection.from_llm,
        DefaultVariableCollection.from_llm,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Data Structures",
        DefaultDataStructureRawSymbolCollection.from_llm,
        DefaultDataStructureCollection.from_llm,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Functions",
        DefaultFnRawSymbolCollection.from_llm,
        DefaultFnCollection.from_llm,
        None,
    ),
]
