from utils.lang_specialization.assembly import (
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    AssemblyDataStructureRawSymbolCollection,
    AssemblyMacroRawSymbolCollection,
    AssemblySubroutineRawSymbolCollection,
    AssemblyVariableRawSymbolCollection,
    data_structure_dict_from_llm_assembly,
    fn_dict_from_llm_assembly,
    macro_dict_from_llm_assembly,
    variables_dict_from_llm_assembly,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_ASSEMBLY = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
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
        S.LLM_COND_JSON,
        "# Global Variables",
        AssemblyVariableRawSymbolCollection.from_llm,
        variables_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Data Structures",
        AssemblyDataStructureRawSymbolCollection.from_llm,
        data_structure_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Subroutines",
        AssemblySubroutineRawSymbolCollection.from_llm,
        fn_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Macros",
        AssemblyMacroRawSymbolCollection.from_llm,
        macro_dict_from_llm_assembly,
        None,
    ),
]
