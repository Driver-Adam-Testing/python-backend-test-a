import json
import pytest
import httpx
import unittest

from src.main import exec_onboarding_service, handler
from src.utils.config import settings

@pytest.fixture
def sns_event():
    """Generates a mock SNS event"""
    return {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps({
                        "Records": [
                            {
                                "s3": {
                                    'eventVersion': '2.1', 
                                    'eventSource': 'aws:s3', 
                                    'awsRegion': 'us-east-1', 
                                    'eventTime': '2024-06-22T01:42:38.304Z', 
                                    'eventName': 'ObjectCreated:Put', 
                                    'userIdentity': {'principalId': 'AWS:AROAYAE342GK2FWTYKKDE:jesse.goeglein'}, 
                                    'requestParameters': {'sourceIPAddress': '98.142.217.111'}, 
                                    'responseElements': {
                                        'x-amz-request-id': 'M4GJ5SBW63F1MB0V', 
                                        'x-amz-id-2': '4Ze44paMbUSOuLEE42gQiSH+dKnPlHPO+ynTVFY5E6KpX23Xl/WwzK5BbOoe90LjYqyU4IykEpIC+1KpJvIhsjpO9L6VVSUk'
                                    },
                                    's3SchemaVersion': '1.0', 
                                    'configurationId': 'code-drop', 
                                    'bucket': {'name': 'development-codebase-dropzone', 'ownerIdentity': {'principalId': 'A3AP0FXFCX5FDS'}, 'arn': 'arn:aws:s3:::development-codebase-dropzone'}, 
                                    'object': {'key': 'codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/infinity-core.zip', 'size': 410874, 'eTag': '5085b4754abeb4757e9e7908dfbf0ea5', 'versionId': 'gblAjwjEGfGtAmJE8PYITDFCkuR8UAJv', 'sequencer': '0066762C0E2E8BABFD'}}
                            }
                        ]
                    })
                }
            }
        ]
    }


@pytest.mark.asyncio
async def test_lambda_handler(sns_event):
    # Assuming the environment and AWS resources are mocked appropriately
    response = await handler(sns_event, {})
    assert response == "OK", "Handler response should be 'Ok'"


# @pytest.mark.asyncio
# async def test_exec_onboarding_service():
#     response = await exec_onboarding_service({"test": "event"})
#     assert response.json()['status'] == "OK", "API call should return 'Ok'"


if __name__ == '__main__':
    unittest.main()
