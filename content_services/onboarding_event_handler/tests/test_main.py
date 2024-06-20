import json
import pytest
import httpx
import unittest

from src.main import lambda_handler
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
