from utils.lang_specialization.assembly import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
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
from utils.lang_specialization.default import default_imports_checker
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_ASSEMBLY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
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
