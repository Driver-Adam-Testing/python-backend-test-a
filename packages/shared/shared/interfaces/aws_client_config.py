from pydantic import BaseModel


class AWSClientConfig(BaseModel):
    region_name: str
