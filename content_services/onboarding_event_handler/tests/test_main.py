import json
import pytest
import httpx
import unittest

from src.main import exec_onboarding_service, handler
from src.config import settings

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
                                    "bucket": {
                                        "name": "test-bucket"
                                    },
                                    "object": {
                                        "key": "test-file.txt"
                                    }
                                }
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
