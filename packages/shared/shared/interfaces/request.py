from pydantic import BaseModel


class DriverRequest(BaseModel):
    pass


class DriverResponse(BaseModel):
    pass


class ModalDriverResponse(DriverResponse):
    call_id: str
