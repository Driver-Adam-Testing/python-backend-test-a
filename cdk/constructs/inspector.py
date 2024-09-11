from constructs import Construct


class InspectorParams:
    environment: str

    def __init__(self, environment):
        self.environment = environment


class Inspector(Construct):
    def __init__(self, scope: Construct, id: str, params: InspectorParams):
        super().__init__(scope, id)

        # This is already being created in the base infra stacks.
        # That creation was added there before the inspector code
        # had been moved within this repository.
        # At some point, we should migrate CDK ownership of the existing
        # inspector buckets into here so that the code and infra all
        # lives in one place, but there are few steps to effecting that
        # safely between different CDK stacks/repos.
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/refactor-stacks.html
        # https://xebia.com/blog/migrate-resources-across-cdk-stacks/
        # self.inspector_bucket = aws_s3.Bucket(
        #     self,
        #     "InspectorBucket",
        #     block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
        #     encryption=aws_s3.BucketEncryption.S3_MANAGED,
        #     enforce_ssl=True,
        # )
