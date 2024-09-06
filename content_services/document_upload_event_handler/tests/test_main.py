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


@pytest.fixture
def real_sns_event():
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "763f6734-ab45-596e-90af-3860e1a28d3c",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-06T00:11:18.267Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"70.123.26.135"},"responseElements":{"x-amz-request-id":"JK043TC0G1HJ1602","x-amz-id-2":"e7jdrMyXuRI1EF2YEJzREbM9tOZmZ1/Ow0Nqmffl51TXTvlizSSINuvNh5VmQFUbnTRhPfR+yrDQKFqE/Ey8PG1RVe06f1Y/"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/paths_output.pdf","size":140400,"eTag":"4b8551c48387d81c247120e4ae25d336","versionId":"CESwjxYp.EwSxaDhMbKaaE_UnEhp4EEx","sequencer":"0066DA48A631D98F96"}}}]}',
                    "Timestamp": "2024-09-06T00:11:19.656Z",
                    "SignatureVersion": "1",
                    "Signature": "SMze9hbK4H4C6mAssYTSY1THUi0pycF3Pb6peICab1wuc0UvwkXcug9NgAztg/t2yXUXSTZBto6rGa7/H4CaQ1whdMadyRxxtA5xDyxqfV2G4dY7ajWYfqhDCf0OwA0u7+/X40a/XVXDfYHdbPOA9F5YdkZwHgpZ/K/Lxas8ZsUAOc4B0yUPQtCRIG7j7ch/o6RQGrE47tCUcNdI6M/LwzJGZXx95XRzsmnE9Vr4eIw2okkdsZFHr1rzs+/aNvMnmZzPiGd8lp+J1TUV3Olso+59lh6GgvjF6KbgTRDM9O5rsNX20XBkb0ZKUlaohJuecc98gtJ67bdayG9+t0Mxgg==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                    "MessageAttributes": {},
                },
            }
        ]
    }


@pytest.fixture
def escape_pdf_name_sns_event():
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "9331655e-f7c3-5dab-9c8f-3a0a98b3dd43",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-06T02:47:11.318Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"70.123.26.135"},"responseElements":{"x-amz-request-id":"Z7JKDEV4R8N887D2","x-amz-id-2":"PqJN412Cs48OLqbO1gQQkaTm/+w/+JYnZHISY69OV2RfHjOC65XSX/lymg10utikoZ7geBlBPSSU+ToD6QLn2TqmAMQ3z/VI"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/pyadi-iio_%2BDevice%2BSpecific%2BPython%2BInterfaces%2BFor%2BIIO%2BDrivers%2B%255BAnalog%2BDevices%2BWiki%255D.pdf","size":262311,"eTag":"cc6c72ee1fdc77e02404fce331790ae6","versionId":".AndLC5Du_ggCvc1tyD5AwJIdOtgij7A","sequencer":"0066DA6D2F40E8B061"}}}]}',
                    "Timestamp": "2024-09-06T02:47:12.445Z",
                    "SignatureVersion": "1",
                    "Signature": "IwogCs6Ky3cmnBYJyydVdrtVqls5DLyFemQuP9sU+LWm9759/VjUaI0r7zljtTQzAPzQjS1AAD6R3AYn/yhfW5kg/nLtixAJRd+NBZQewbF0A52ZJhDQ4RkYVevs12atJu1RAzvEVczHhDKvpdaDM8t/LQv9POeld212ChVaQBkFD54KAGhy2AVfMLJGRAObtMR/M+o2wvWtpj1K8CfJHVUWlZisfvZmvsZZrU0xMIXvqL0xJDTnhtXG0LVcpYqtK24aTHP6RheSouBAhf1WQZaYDnZWjMPy1/CHM5qJNgIYxQSJtfJd4bO4n46Dpy/7uxOg82ekU1mFW1e2EhtPTQ==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                    "MessageAttributes": {},
                },
            }
        ]
    }


def test_document_upload_lambda_handler(sns_event):
    # Assuming the environment and AWS resources are mocked appropriately
    response = handler(sns_event, {})
    assert isinstance(response, list), "Handler response should be a list"
    assert len(response) > 0, "Handler response list should not be empty"
    for result in response:
        assert (
            "source_content_id" in result
        ), "Result should contain 'source_content_id'"
        assert "bucket" in result, "Result should contain 'bucket'"
        assert "key" in result, "Result should contain 'key'"
        assert (
            "pdf_summary_response" in result
        ), "Result should contain 'pdf_summary_response'"
        assert (
            result["pdf_summary_response"] == "OK"
        ), "PDF summary response should be 'OK'"


def test_real_document_upload_lambda_handler(real_sns_event):
    response = handler(real_sns_event, {})
    assert isinstance(response, list), "Handler response should be a list"
    assert len(response) > 0, "Handler response list should not be empty"
    for result in response:
        assert (
            "source_content_id" in result
        ), "Result should contain 'source_content_id'"
        assert "bucket" in result, "Result should contain 'bucket'"
        assert "key" in result, "Result should contain 'key'"
        assert (
            "pdf_summary_response" in result
        ), "Result should contain 'pdf_summary_response'"
        assert (
            result["pdf_summary_response"] == "OK"
        ), "PDF summary response should be 'OK'"


def test_escape_pdf_name_document_upload_lambda_handler(escape_pdf_name_sns_event):
    response = handler(escape_pdf_name_sns_event, {})
    assert isinstance(response, list), "Handler response should be a list"
    assert len(response) > 0, "Handler response list should not be empty"
    for result in response:
        assert (
            "source_content_id" in result
        ), "Result should contain 'source_content_id'"
        assert "bucket" in result, "Result should contain 'bucket'"
        assert "key" in result, "Result should contain 'key'"
        assert (
            "pdf_summary_response" in result
        ), "Result should contain 'pdf_summary_response'"
        assert (
            result["pdf_summary_response"] == "OK"
        ), "PDF summary response should be 'OK'"


if __name__ == "__main__":
    unittest.main()
