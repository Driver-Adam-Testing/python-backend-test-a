from utils.lang_specialization.verilog import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG,
    VerilogFnTaskCollection,
    VerilogFnTaskRawSymbolCollection,
    VerilogModuleCollection,
    VerilogModuleRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_VERILOG = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG,
        SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    ),
    (
        S.FN_COND_JSON,
        "# Modules",
        VerilogModuleRawSymbolCollection.from_static_analysis,
        VerilogModuleCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions and Tasks",
        VerilogFnTaskRawSymbolCollection.from_static_analysis,
        VerilogFnTaskCollection.from_llm,
        None,
    ),
]
