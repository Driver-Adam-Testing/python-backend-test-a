from utils.lang_specialization.c_sharp import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
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
from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_CS = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
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
