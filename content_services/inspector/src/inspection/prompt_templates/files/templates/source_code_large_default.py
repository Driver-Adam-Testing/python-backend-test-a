from utils.lang_specialization.default import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    DefaultDataStructureRawSymbolCollection,
    DefaultFnRawSymbolCollection,
    DefaultVariableRawSymbolCollection,
    data_structure_dict_from_llm_default,
    default_imports_checker,
    fn_dict_from_llm_default,
    variables_dict_from_llm_default,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_DEFAULT = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
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
        S.LLM_COND_JSON,
        "# Global Variables",
        DefaultVariableRawSymbolCollection.from_llm,
        variables_dict_from_llm_default,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Data Structures",
        DefaultDataStructureRawSymbolCollection.from_llm,
        data_structure_dict_from_llm_default,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Functions",
        DefaultFnRawSymbolCollection.from_llm,
        fn_dict_from_llm_default,
        None,
    ),
]
