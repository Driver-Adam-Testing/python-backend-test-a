from pydantic import BaseModel


class AWSClientConfig(BaseModel):
    region_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
