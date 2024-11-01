from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
)
from utils.lang_specialization.verilog import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG,
    VerilogFnTaskRawSymbolCollection,
    VerilogModuleRawSymbolCollection,
    function_task_dict_from_llm_verilog,
    module_dict_from_llm_verilog,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_VERILOG = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.FN_COND_JSON,
        "# Modules",
        VerilogModuleRawSymbolCollection.from_static_analysis,
        module_dict_from_llm_verilog,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions and Tasks",
        VerilogFnTaskRawSymbolCollection.from_static_analysis,
        function_task_dict_from_llm_verilog,
        None,
    ),
]
