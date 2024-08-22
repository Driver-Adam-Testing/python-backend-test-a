from fastapi import APIRouter
from pydantic import BaseModel
from shared.agent.agent_factory import create_agent

router = APIRouter()


class GenerateRequest(BaseModel):
    workspace_id: str
    prompt: str
    codebase_id: str | None = None
    model: str | None = None
    max_iterations: int = 1


@router.post(
    "/",
    summary="Generate content based on the provided prompt",
    response_description="Return generated content",
)
def generate_content(request: GenerateRequest):
    """
    ## Generate content
    Returns:
        str: Returns the generated content
    """

    agent = create_agent(
        workspace_id=request.workspace_id,
        codebase_id=request.codebase_id,
        model=request.model,
        max_iterations=request.max_iterations,
    )

    prompt = request.prompt

    result = agent.invoke(prompt)

    if result.startswith("```markdown") and result.endswith("```"):
        result = result[11:-3]

    return {"generated_content": result}
