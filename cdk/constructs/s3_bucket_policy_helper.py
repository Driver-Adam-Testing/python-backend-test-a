import json
from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
)

class S3BucketPolicyHelper:
    def __init__(self, scope: Construct, bucket: s3.IBucket) -> None:
        self.scope = scope
        self.bucket = bucket

    def apply_raw_policy(self, policy_json: str) -> None:
        """
        Takes a raw bucket policy JSON string and applies all its statements
        to the bucket's resource policy.
        """
        policy = json.loads(policy_json)

        statements = policy.get("Statement", [])
        for stmt in statements:
            statement = iam.PolicyStatement.from_json(stmt)
            self.bucket.add_to_resource_policy(statement)