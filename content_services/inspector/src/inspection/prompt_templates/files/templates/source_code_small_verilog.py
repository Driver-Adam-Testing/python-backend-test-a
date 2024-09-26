from utils.lang_specialization.verilog import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG,
    fntask_dict_from_llm_verilog,
    module_dict_from_llm_verilog,
    verilog_fntask_checker,
    verilog_module_checker,
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
        "\n---\n## Modules",
        verilog_module_checker,
        module_dict_from_llm_verilog,
        None,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Functions and Tasks",
        verilog_fntask_checker,
        fntask_dict_from_llm_verilog,
        None,
    ),
]
