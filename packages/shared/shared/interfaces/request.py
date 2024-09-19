from pydantic import BaseModel


class DriverRequest(BaseModel):
    pass


class DriverModalRequest(DriverRequest):
    call_id: str


class DriverModalBatchRequest(DriverRequest):
    call_ids: list[str]
