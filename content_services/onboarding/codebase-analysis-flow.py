import hashlib
import json
import os
import sys
import time

import boto3
import modal
from botocore.exceptions import BotoCoreError, ClientError
from modal.functions import FunctionCall
from src.utils import delete_file_from_s3, parse_presigned_url


AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def generate_get_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def generate_put_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires,
    )


def upload_zip_to_s3(zip_file_path: str, bucket: str, key: str) -> dict:
    try:
        s3_client.upload_file(zip_file_path, bucket, key)
        # Verify upload
        s3_client.head_object(Bucket=bucket, Key=key)
        return {"status": "success", "bucket": bucket, "key": key}
    except (BotoCoreError, ClientError) as error:
        return {"status": "error", "error_message": str(error)}


def has_no_threats_tag(bucket: str, key: str) -> bool:
    tags = s3_client.get_object_tagging(Bucket=bucket, Key=key)
    return (
        len(
            [
                tag
                for tag in tags["TagSet"]
                if tag["Key"] == "GuardDutyMalwareScanStatus"
                and tag["Value"] == "NO_THREATS_FOUND"
            ]
        )
        == 1
    )


def org_id_to_hash(organization_id: str) -> str:
    return hashlib.sha256(organization_id.encode()).hexdigest()[:63]


def build_object_key(org_id_hash: str, file_name: str) -> str:
    return f"analysis/{org_id_hash}/{file_name}"


def extract_file_name(file_path: str) -> str:
    return os.path.basename(file_path)


def poll_modal(call_id: str) -> dict:
    function_call = FunctionCall.from_id(call_id)

    result = {
        "call_id": call_id,
        "status": "pending",
        "response": None,
        "error": "",
    }
    try:
        response = function_call.get(timeout=0)
        result["response"] = response
        result["status"] = "completed"
    except TimeoutError:
        result["status"] = "running"
    except Exception as e:
        result["status"] = "expired"
        result["error"] = str(e)

    return result


def wait_for_modal_jon(
    call_id: str, timeout: int = 60, interval: int = 5
) -> dict | None:
    start_time = time.time()
    print(f"Starting to poll for 'modal' for '{call_id}'.")
    print(f"Timeout set to {timeout} seconds, checking every {interval} seconds.")

    while (time.time() - start_time) < timeout:
        result = poll_modal(call_id)
        if result["status"] == "completed":
            print(f"Modal completed for '{call_id}'.")
            return result
        print(f"Modal still running for '{call_id}'.")
        print(f"Current status: {result['status']}")
        time.sleep(interval)
    print(f"Timeout reached for '{call_id}'.")
    return None


ORG_ID = "org_s76pU1v8LAYhTOWB"
BUCKET_NAME = "development-codebase-dropzone"


def main(file_path: str):
    """
    1. Extract file name from file path
    2. Build object key
    3. Generate presigned url
    4. Upload file to s3
    5. Run pre codebase analysis
    6. Wait for modal to complete
    7. Delete file from s3
    """
    file_name = extract_file_name(file_path)
    object_key = build_object_key(org_id_to_hash(ORG_ID), file_name)
    download_url = generate_get_presigned_url(BUCKET_NAME, object_key)

    bucket, object_key = parse_presigned_url(download_url)


    upload_zip_to_s3(file_path, BUCKET_NAME, object_key)

    run_pre_codebase_analysis = modal.Function.lookup(
        "codebase-onboarding", "run_pre_codebase_analysis", environment_name="dev-eric"
    )

    print("Running Pre Codebase Analysis...")
    instance = run_pre_codebase_analysis.spawn(download_url)
    call_id = instance.object_id

    modal_response = wait_for_modal_jon(call_id)
    r = modal_response["response"]
    parsed_dict = json.loads(r)
    print(f"codebase analysis complete for: {file_name} \n")
    print(json.dumps(parsed_dict, indent=4))
    print("deleting file from s3...")
    delete_file_from_s3(object_key, BUCKET_NAME)


if __name__ == "__main__":
    main(sys.argv[1])
