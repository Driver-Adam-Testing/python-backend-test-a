from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from cdk.constructs.backend import Backend
from constructs import Construct

class DevelopmentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backend = Backend(self, "ApiDataStores")
