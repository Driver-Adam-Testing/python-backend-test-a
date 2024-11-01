from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.java import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA,
    JavaClassRawSymbolCollection,
    JavaInterfaceRawSymbolCollection,
    class_dict_from_llm_java,
    interface_dict_from_llm_java,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_JAVA = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        JavaInterfaceRawSymbolCollection.from_static_analysis,
        interface_dict_from_llm_java,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        JavaClassRawSymbolCollection.from_static_analysis,
        class_dict_from_llm_java,
        None,
    ),
]
