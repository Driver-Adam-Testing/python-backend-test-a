from datetime import timedelta

import openai
from autodocs.src.autodoc_log import AutoDocLog, write_autodoc_log
from autodocs.src.utils.models import ChatOpenAI
from hatchet_client import hatchet
from hatchet_sdk import Context
from pydantic import BaseModel


class LLMGenerateInput(BaseModel):
    model: str
    system_prompt: str
    user_prompt: str


class WriteAutoDocLogInput(BaseModel):
    log: AutoDocLog


async def llm_generate_hatchet(model: str, system_prompt: str, user_prompt: str) -> str:
    try:
        llm = ChatOpenAI(model=model, temperature=0, request_timeout=900)
        return await llm.generate_response(
            system_prompt=system_prompt, user_prompt=user_prompt
        )
    except openai.BadRequestError:
        print(f"Bad request error for {user_prompt[:1000]}")
        return ""


@hatchet.task(name="llm-generate-workflow", execution_timeout=timedelta(minutes=15))
async def llm_generate_task(input: LLMGenerateInput, ctx: Context) -> dict:
    print("starting llm generate task")
    result = await llm_generate_hatchet(
        model=input.model,
        system_prompt=input.system_prompt,
        user_prompt=input.user_prompt,
    )
    print("executed llm generate task")
    return {"result": result}


@hatchet.task(name="write-autodoc-log-workflow", execution_timeout=timedelta(minutes=5))
def write_autodoc_log_task(input: WriteAutoDocLogInput, ctx: Context) -> None:
    print("starting write autodoc log task")
    write_autodoc_log(input.log)
    print("executed write autodoc log task")
