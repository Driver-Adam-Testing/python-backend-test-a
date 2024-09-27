from utils.lang_specialization.verilog import (
    FUNCTIONS_AND_TASKS_NONE_CONTENT,
    MODULES_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG,
    fntask_dict_from_llm_verilog,
    module_dict_from_llm_verilog,
    verilog_fntask_checker,
    verilog_module_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_VERILOG = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (S.RAW, "# Symbol Documentation"),
    (
        S.FN_COND_JSON,
        "# Modules",
        verilog_module_checker,
        module_dict_from_llm_verilog,
        MODULES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "# Functions and Tasks",
        verilog_fntask_checker,
        fntask_dict_from_llm_verilog,
        FUNCTIONS_AND_TASKS_NONE_CONTENT,
    ),
]
