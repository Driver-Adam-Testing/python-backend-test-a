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
                    "MessageId": "943c741e-b91b-599a-afb3-2b441b6c065b",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-10T19:38:30.682Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"70.123.26.135"},"responseElements":{"x-amz-request-id":"FG4GEVAPSVK6WFD4","x-amz-id-2":"4bGCWNdQFM4GsS+Wzug+xPnkR2vJRVBDZkUFxIPCgT2XI/mqKJ/9yDlAiNrjIceXpMog3RwLCUucYh/e1McW410Nam1LzHlA"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/f07e2ce5-3679-4f6b-b509-03aa233ae314_SG_Slow_Query_Analysis_SG_driverai_dev3_aws_64085.servers.mongodirector.com__Aug_05_18_38__UTC____Aug_06_17_38__UTC_.pdf","size":81162,"eTag":"d8c563249474d93c5bc210fd5f2a6656","versionId":"qTFya.xu1iJcQarccGkKLK.EDyuiLsOI","sequencer":"0066E0A0369C149E17"}}}]}',
                    "Timestamp": "2024-09-10T19:38:31.959Z",
                    "SignatureVersion": "1",
                    "Signature": "JyJjHs4hvekcV3PfGbvOT+VhB0iQ6XPnU69AgpQ6UkkX61c4mxlIoJTnVZY1b225VD7VJX3XIUrJ4HE6kO5eL1ng4LvZ+ybjV7Mi0fUKesnt94kdvz2uRdk29c1xp8dRI2bhB/g/MjDsZHmUXIHTkmGz+yWbj7ls4sdyRkqNy6qdYbYwGKD7ooMga7FtgDtyyrB9+EOY5vvivBvgUWsxRz/JtoUu5Mj0nDs35cIKwXQJwhE6S+0Ko3DPbObnZLBawHs4cg3BDzqe4gFiyq3VPTdK9ypKB4x0yP1eBG5d2z4vg13Tyz819VsC4xMc1sFfbuXnwU7PldzAR7AEA9FxBA==",
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
                    "MessageId": "f4c9007b-6738-5647-921f-5f2e24a63f4b",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-06T17:52:28.924Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"65.201.88.74"},"responseElements":{"x-amz-request-id":"G2Z8P9X2XFKWE6T4","x-amz-id-2":"O9mZ32Y9/++mn75g4imVxMJa2xJl8lu+3oQhzGfA6us1p0WzO1vPWq2hJjE4JSRVt48dCh9gVJeN1ZjcAnmVaQjvXxg76OWC"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/pyadi-iio_%2BDevice%2BSpecific%2BPython%2BInterfaces%2BFor%2BIIO%2BDrivers%2B%255BAnalog%2BDevices%2BWiki%255D.pdf","size":262311,"eTag":"cc6c72ee1fdc77e02404fce331790ae6","versionId":"ohtNdMFSAZMZqyA.j5kkgrFpW_C1DI.r","sequencer":"0066DB415CCA68F2B5"}}}]}',
                    "Timestamp": "2024-09-06T17:52:30.094Z",
                    "SignatureVersion": "1",
                    "Signature": "qOsf6xjPdwRo9mOVQjklnCkNMstwJ3KVmAr/SZbM7iW2wkVQpJ84OwYg3uHUuDUWHps1W7BjOuWasZrzDHW27s4fVWt7LIL3/IYn2LNlMTUG6WCGavglz3n+5AsfEVmwQq9e1if7l7hBbdzVduTYEQSKeClBcbxe79wkvBnojyBc317YpKrcDwvGBUuExgsy/fglzjTLOpHZWY6R16VHp2z7athxTnv06ifEJvj2eSN0kHmPwgpruga2VTqVS3EA3Xiu3GqqtJfWYTD30Mtu0ERWQYJeGcgkl9ema1EEqIkXMW0pDMPbZJ0/Cd84ygAOteI596/Y4WAk9OL43OKrxw==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                    "MessageAttributes": {},
                },
            }
        ]
    }


@pytest.fixture
def escape_pdf_name_sns_event2():
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "4876799c-951b-57bd-b580-26c9ad806e1d",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-06T17:05:30.349Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"65.201.88.74"},"responseElements":{"x-amz-request-id":"VJVDA67KENEH383Y","x-amz-id-2":"6Xtt703qqkgxG1Gib5lHGaaKd+p4PTxDWGaf0RF8+3nLGKKp33TcflNWu60IN4S2PQ7S8aNjheXUdkBfHW1ukq5l0CxlCIb7"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/pyadi-iio%2BD_evice%2BSpecific%2BPython%2BInterfaces%2BFor%2BIIO%2BDrivers%2B%255BAnalog%2BDevices%2BWiki%255D.pdf","size":262311,"eTag":"cc6c72ee1fdc77e02404fce331790ae6","versionId":"HttUdUgTD6dK.1bABQT7yLZRMeqZDosB","sequencer":"0066DB365A2BEC5530"}}}]}',
                    "Timestamp": "2024-09-06T17:05:31.735Z",
                    "SignatureVersion": "1",
                    "Signature": "CS9cDAUS6ARvW1bIxL+x8Cf1QS4WFfAJWRGLi0dU0pqjoAhINPgSOw5+bm0i9zhAsZEQ9z4+AvzW1Shi8ZsBlQajEoz4S8VsIjeEfKfcaiqwghueSNPKBrD4/gePmgofO+sys9eqO1Ve4hIjYFe5CmNJXpfR13UaC2xD+xWDfobF2rxngt6N5cVb80OvqQET/yNYnljqjfP2E1XWvvYUwXiMlkkmZjhK0iF61TpWd/Gnx6AdL1d5ddfg+tHSe1SKycWbdWoP6sOmqY4ItFceZNcHRJzZbvJzr5z1sd8NqqOigw6GlxYbgFve7D9FTAB+BzW6F/uIBiEZGAEWOULFUA==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                    "MessageAttributes": {},
                },
            }
        ]
    }


@pytest.fixture
def pdf_name_with_whitespace_sns_event():
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "e4adf322-79be-58cf-823e-ac77622302c3",
                    "TopicArn": "arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq",
                    "Subject": "Amazon S3 Notification",
                    "Message": '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2024-09-06T15:01:47.949Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAYAE342GKYWJN6UVW7"},"requestParameters":{"sourceIPAddress":"65.201.88.74"},"responseElements":{"x-amz-request-id":"KSCVQZPV1WABH47P","x-amz-id-2":"8gn5i1hDSKYyBNAxIpsVNQIAeoOTDh5SzNUvv1aLj7Dp/r0+qMd1ptoIeKRixmFAgRjC968UkhXoWWxpjxWrrweZBy07tL26"},"s3":{"s3SchemaVersion":"1.0","configurationId":"file-drop","bucket":{"name":"development-codebase-dropzone","ownerIdentity":{"principalId":"A3AP0FXFCX5FDS"},"arn":"arn:aws:s3:::development-codebase-dropzone"},"object":{"key":"documents/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/Basic+Document+Reference+Tracking.pdf","size":1172539,"eTag":"aac3975a3073a7180cfe0cc13016af6a","versionId":"Izbsxbr8In7aL.wYGmOZU_jpZD.gcp79","sequencer":"0066DB195BD59E3C47"}}}]}',
                    "Timestamp": "2024-09-06T15:01:49.367Z",
                    "SignatureVersion": "1",
                    "Signature": "KpXjtwL6VP59iZL9kxWaZPk2y+iWgVkcUDYIS/zZPWLrB7QuDwC+DbpysbJdre7omMyyCRaGqW/6qlQarYRfrjbzRU/j/MWvZxyRKoK0GAAC03O+zuHxpEOfLxZRRliEDVBaKX4IooWNaCKFXrWNSMR36KScMkWtJPsbk/BWD7TELbFTGg77kd3+UnRAWDTe7r1d6lxfU/SY6k2vHIou0HTbftPrG9IXIojXydBOebDJjoG6twDjFX9v7rSoqovx3Y5EzzWnCM9whATsExuHj90oudKR8ljwAmbYY1+BMqZn7NxjerNmWdH4jHzvs5Z9btK53zNf4sAjUSXHiKwaMw==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:550082761109:CdkInfraStackCodebaseOnboardingLambdaStackE7027C30-TopicBFC7AF6E-T41t4VpPQduq:33410862-0d11-4c7d-a93c-39d27f43b269",
                    "MessageAttributes": {},
                },
            }
        ]
    }


# def test_document_upload_lambda_handler(sns_event):
#     """
#     Test the document upload lambda handler with a mock SNS event.
#
#     This test checks if the handler returns a list of results, and each result contains
#     the expected keys and values.
#     """
#     # Assuming the environment and AWS resources are mocked appropriately
#     response = handler(sns_event, {})
#     assert isinstance(response, list), "Handler response should be a list"
#     assert len(response) > 0, "Handler response list should not be empty"
#     for result in response:
#         assert (
#             "source_content_id" in result
#         ), "Result should contain 'source_content_id'"
#         assert "bucket" in result, "Result should contain 'bucket'"
#         assert "key" in result, "Result should contain 'key'"
#         assert (
#             "pdf_summary_response" in result
#         ), "Result should contain 'pdf_summary_response'"
#         assert (
#             result["pdf_summary_response"] == "OK"
#         ), "PDF summary response should be 'OK'"
#


def test_real_document_upload_lambda_handler(real_sns_event):
    """
    Test the document upload lambda handler with a real SNS event.

    This test checks if the handler returns a list of results, and each result contains
    the expected keys and values.
    """
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


if __name__ == "__main__":
    unittest.main()
