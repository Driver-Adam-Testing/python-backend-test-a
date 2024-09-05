from aws_cdk import (
    aws_s3,
)
from constructs import Construct


class InspectorParams:
    environment: str

    def __init__(self, environment):
        self.environment = environment


class Inspector(Construct):
    def __init__(self, scope: Construct, id: str, params: InspectorParams):
        super().__init__(scope, id)

        self.inspector_bucket = aws_s3.Bucket(
            self,
            "InspectorBucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )
