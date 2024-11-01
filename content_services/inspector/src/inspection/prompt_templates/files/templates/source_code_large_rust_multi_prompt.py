from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.rust import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
    RustDataStructureRawSymbolCollection,
    RustFnRawSymbolCollection,
    RustMacroRawSymbolCollection,
    RustTraitsRawSymbolCollection,
    RustVariablesRawSymbolCollection,
    data_structure_dict_from_llm_rust,
    fn_dict_from_llm_rust,
    macros_dict_from_llm_rust,
    traits_dict_from_llm_rust,
    variables_dict_from_llm_rust,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
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
        "# Global Variables",
        RustVariablesRawSymbolCollection.from_static_analysis,
        variables_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Macros",
        RustMacroRawSymbolCollection.from_static_analysis,
        macros_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Traits",
        RustTraitsRawSymbolCollection.from_static_analysis,
        traits_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        RustDataStructureRawSymbolCollection.from_static_analysis,
        data_structure_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        RustFnRawSymbolCollection.from_static_analysis,
        fn_dict_from_llm_rust,
        None,
    ),
]
