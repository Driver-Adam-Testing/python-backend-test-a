import json
import boto3


def lambda_handler(event, context):
    # Parse the SNS message
    for record in event['Records']:
        sns_message = json.loads(record['Sns']['Message'])

        # Extract information from the S3 event
        for s3_record in sns_message['Records']:
            bucket_name = s3_record['s3']['bucket']['name']
            object_key = s3_record['s3']['object']['key']

            # Execute API call to run the onboarding service
            run_onboarding_service(bucket_name, object_key)


def run_onboarding_service(bucket, key):
    # Placeholder for the API call logic
    print(f"Running onboarding service for {bucket}/{key}")

# Ensure you have the necessary permissions in your Lambda's execution role to read from S3 and SNS
# TODO: this service receives events from s3 when objects are uploaded
# 1. It should be able to handle the event
# 2. It should be able to parse the event
# 3. It should be able to extract the object key
#4. It should be able to execute an api call to run the onboarding service
