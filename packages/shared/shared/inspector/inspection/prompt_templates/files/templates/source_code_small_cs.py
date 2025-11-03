from shared.inspector.utils.lang_specialization.c_sharp import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CS,
    CsClassCollection,
    CsClassRawSymbolCollection,
    CsInterfaceCollection,
    CsInterfaceRawSymbolCollection,
    CsStructCollection,
    CsStructRawSymbolCollection,
)
from shared.inspector.utils.lang_specialization.default import (
    default_imports_checker,
)
from shared.inspector.utils.templates import S
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

SOURCE_CODE_SMALL_TEMPLATE_CS = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CS))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        CsClassRawSymbolCollection.from_static_analysis,
        CsClassCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Structs",
        CsStructRawSymbolCollection.from_static_analysis,
        CsStructCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        CsInterfaceRawSymbolCollection.from_static_analysis,
        CsInterfaceCollection.from_llm,
        None,
    ),
]
