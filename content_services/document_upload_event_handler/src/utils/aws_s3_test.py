import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from src.utils.aws_s3 import (
    copy_s3_object,
    ensure_bucket_exists,
    generate_get_presigned_url,
    head_object,
)


@pytest.fixture
def s3_setup(monkeypatch):
    with mock_aws():
        # Set dummy AWS credentials
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake_access_key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake_secret_key")
        monkeypatch.setenv("AWS_SESSION_TOKEN", "fake_session_token")

        s3 = boto3.client("s3", region_name="us-east-1")
        source_bucket = "source-bucket"
        dest_bucket = "dest-bucket"
        source_key = "source-key"
        dest_key = "dest-key"
        s3.create_bucket(Bucket=source_bucket)
        s3.create_bucket(Bucket=dest_bucket)
        s3.put_object(Bucket=source_bucket, Key=source_key, Body="Test content")
        yield s3, source_bucket, source_key, dest_bucket, dest_key


def test_copy_s3_object(s3_setup, monkeypatch):
    s3, source_bucket, source_key, dest_bucket, dest_key = s3_setup
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = copy_s3_object(source_bucket, source_key, dest_bucket, dest_key)
    assert result
    copied_object = s3.get_object(Bucket=dest_bucket, Key=dest_key)
    assert copied_object["Body"].read().decode("utf-8") == "Test content"


def test_copy_non_existent_source_object(s3_setup, monkeypatch):
    s3, source_bucket, _, dest_bucket, dest_key = s3_setup
    non_existent_key = "non-existent-key"
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = copy_s3_object(source_bucket, non_existent_key, dest_bucket, dest_key)
    assert not result


def test_copy_non_existent_source_bucket(s3_setup, monkeypatch):
    s3, _, source_key, dest_bucket, dest_key = s3_setup
    non_existent_bucket = "non-existent-bucket"
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = copy_s3_object(non_existent_bucket, source_key, dest_bucket, dest_key)
    assert not result


def test_copy_non_existent_dest_bucket(s3_setup, monkeypatch):
    s3, source_bucket, source_key, _, dest_key = s3_setup
    non_existent_bucket = "non-existent-bucket"
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = copy_s3_object(source_bucket, source_key, non_existent_bucket, dest_key)
    assert not result


def test_generate_get_presigned_url(s3_setup, monkeypatch):
    s3, source_bucket, source_key, _, _ = s3_setup
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)  # Mock the s3_client
    url = generate_get_presigned_url(source_bucket, source_key)
    assert url.startswith("https://")


def test_head_object(s3_setup, monkeypatch):
    s3, source_bucket, source_key, _, _ = s3_setup
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    response = head_object(source_bucket, source_key)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_ensure_bucket_exists(s3_setup, monkeypatch):
    s3, _, _, _, _ = s3_setup
    new_bucket = "new-bucket"
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = ensure_bucket_exists(new_bucket)
    assert result
    response = s3.head_bucket(Bucket=new_bucket)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_ensure_bucket_exists_already_exists(s3_setup, monkeypatch):
    s3, source_bucket, _, _, _ = s3_setup
    monkeypatch.setattr("src.utils.aws_s3.s3_client", s3)
    result = ensure_bucket_exists(source_bucket)
    assert result
    response = s3.head_bucket(Bucket=source_bucket)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_ensure_bucket_exists_creation_failure(mocker):
    mocker.patch("boto3.client", side_effect=Exception("Creation failed"))
    with pytest.raises(ClientError):
        ensure_bucket_exists("new-bucket")
