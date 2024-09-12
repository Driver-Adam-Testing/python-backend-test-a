import json
import unittest

import pytest
from src.main import handler


@pytest.fixture
def sns_event():
    """Generates a mock SNS event"""
    return {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps(
                        {
                            "Records": [
                                {
                                    "s3": {
                                        "eventVersion": "2.1",
                                        "eventSource": "aws:s3",
                                        "awsRegion": "us-east-1",
                                        "eventTime": "2024-06-22T01:42:38.304Z",
                                        "eventName": "ObjectCreated:Put",
                                        "userIdentity": {
                                            "principalId": "AWS:AROAYAE342GK2FWTYKKDE:jesse.goeglein"
                                        },
                                        "requestParameters": {
                                            "sourceIPAddress": "98.142.217.111"
                                        },
                                        "responseElements": {
                                            "x-amz-request-id": "M4GJ5SBW63F1MB0V",
                                            "x-amz-id-2": "4Ze44paMbUSOuLEE42gQiSH+dKnPlHPO+ynTVFY5E6KpX23Xl/WwzK5BbOoe90LjYqyU4IykEpIC+1KpJvIhsjpO9L6VVSUk",
                                        },
                                        "s3SchemaVersion": "1.0",
                                        "configurationId": "code-drop",
                                        "bucket": {
                                            "name": "local-codebase-dropzone",
                                            "ownerIdentity": {
                                                "principalId": "A3AP0FXFCX5FDS"
                                            },
                                            "arn": "arn:aws:s3:::local-codebase-dropzone",
                                        },
                                        "object": {
                                            "key": "documents/e899ee0c4a104b64d6c3683636bddda7c3717c38180ff21a3a93049caf6a879/AD4114-1.pdf",
                                            "size": 813572,
                                            "eTag": "8b0ba2f009511f6c218bea1ee7c4ce22",
                                            "sequencer": "0066D20F581EFCB508",
                                        },
                                    }
                                }
                            ]
                        }
                    )
                }
            }
        ]
    }


def test_document_upload_lambda_handler(sns_event):
    # Assuming the environment and AWS resources are mocked appropriately
    # print("YYYY")
    response = handler(sns_event, {})
    assert response == "OK", "Handler response should be 'OK'"
    # assert True


if __name__ == "__main__":
    unittest.main()
