from pydantic import BaseModel


class UsageEventMetadata(BaseModel):
    model: str
    provider: str
    model_price: float | None = None
    input: dict
    output: dict
