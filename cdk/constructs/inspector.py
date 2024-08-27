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

        inspector = aws_s3.Bucket.from_bucket_name(
            scope, "inspector-bucket", params.environment + "-dai-inspector-bucket"
        )
