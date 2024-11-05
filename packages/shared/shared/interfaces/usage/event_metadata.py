from pydantic import BaseModel


class UsageEventMetadata(BaseModel):
    model: str
    provider: str
    model_price: float
    input: dict
    output: dict
