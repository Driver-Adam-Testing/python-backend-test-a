from utils.lang_specialization.c_sharp import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS,
    CsClassCollection,
    CsClassRawSymbolCollection,
    CsInterfaceCollection,
    CsInterfaceRawSymbolCollection,
    CsStructCollection,
    CsStructRawSymbolCollection,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CS = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
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
