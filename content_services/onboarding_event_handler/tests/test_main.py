import sys
import os
import json
import pytest
import httpx
import unittest
from httpx import Response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from src.main import lambda_handler
from src.config import settings


# from moto.s3
# from moto.sns import mock_sns
# Add the src directory to the system path


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


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
    response = await lambda_handler(sns_event, {})
    assert response == "OK", "Handler response should be 'Ok'"


@pytest.mark.asyncio
async def test_exec_onboarding_service():
    async with httpx.AsyncClient(base_url=settings.API_URL) as client:
        response = await client.get("/healthcheck/")
        print(response.json())
        assert response.json()['status'] == "OK", "API call should return 'Ok'"


if __name__ == '__main__':
    unittest.main()
