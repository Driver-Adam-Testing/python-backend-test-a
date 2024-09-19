from pydantic import BaseModel


class DriverResponse(BaseModel):
    pass


class DriverModalResponse(DriverResponse):
    call_id: str
