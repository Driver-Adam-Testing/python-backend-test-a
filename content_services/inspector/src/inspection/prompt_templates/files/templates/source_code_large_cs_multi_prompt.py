from utils.lang_specialization.c_sharp import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS,
    CsClassRawSymbolCollection,
    CsEnumRawSymbolCollection,
    CsInterfaceRawSymbolCollection,
    CsStructRawSymbolCollection,
    class_dict_from_llm_cs,
    enum_dict_from_llm_cs,
    interface_dict_from_llm_cs,
    struct_dict_from_llm_cs,
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
        class_dict_from_llm_cs,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Structs",
        CsStructRawSymbolCollection.from_static_analysis,
        struct_dict_from_llm_cs,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        CsInterfaceRawSymbolCollection.from_static_analysis,
        interface_dict_from_llm_cs,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Enums",
        CsEnumRawSymbolCollection.from_static_analysis,
        enum_dict_from_llm_cs,
        None,
    ),
]
