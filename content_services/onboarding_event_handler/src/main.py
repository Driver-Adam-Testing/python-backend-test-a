import json
import httpx
import botocore 
import botocore.session 
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig 
from src.utils.config import settings

# Ensure you have the necessary permissions in your Lambda's execution role to read from S3 and SNS
# TODO: this service receives events from s3 when objects are uploaded
# 1. It should be able to handle the event
# 2. It should be able to parse the event
# 3. It should be able to extract the object key
# 4. It should be able to execute an api call to run the onboarding service

def handler(event, context):
    # Parse the SNS message
    for record in event['Records']:
        sns_message = json.loads(record['Sns']['Message'])

        sm_client = botocore.session.get_session().create_client('secretsmanager')
        cache_config = SecretCacheConfig()
        cache = SecretCache(config = cache_config, client = sm_client)

        access_key_id = cache.get_secret_string(settings.L_AWS_ACCESS_KEY_ID) if settings.ENVIRONMENT != "local" else settings.L_AWS_ACCESS_KEY_ID
        access_key_secret = cache.get_secret_string(settings.L_AWS_ACCESS_KEY_SECRET) if settings.ENVIRONMENT != "local" else settings.L_AWS_ACCESS_KEY_ID
        s3_client = botocore.session.get_session().create_client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_key_secret,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
            if settings.AWS_S3_ENDPOINT_URL
            else None,
        )

        client_id = cache.get_secret_string(settings.CLIENT_ID_SECRET) if settings.ENVIRONMENT != "local" else settings.CLIENT_ID_SECRET
        client_secret = cache.get_secret_string(settings.CLIENT_SECRET_SECRET) if settings.ENVIRONMENT != "local" else settings.CLIENT_SECRET_SECRET
        payload = json.dumps({"client_id":client_id,"client_secret":client_secret,"audience":settings.API_URL,"grant_type":"client_credentials"})
        
        with httpx.Client(base_url=settings.AUTH0_URL) as auth0Client:
            # Fetch one M2M token per invocation of the lambda. This could be cached but would require additional impl similar to SecretCache above
            token_response = auth0Client.post("/oauth/token", headers={ 'content-type': "application/json" }, data=payload)
            token_response.raise_for_status() # Raises an exception for 4XX/5XX responses
            token_json = token_response.json()

            # Extract information from the S3 event
            for s3_record in sns_message['Records']:
                print(s3_record)
                bucket_name = s3_record['s3']['bucket']['name']
                object_key = s3_record['s3']['object']['key']
                metadata = s3_client.head_object(Bucket=bucket_name, Key=object_key)
                print(metadata)
                
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": object_key},
                    ExpiresIn=3600,
                )

                return exec_onboarding_service({ 
                    "download_url": presigned_url, 
                    "object_key": object_key, 
                    "org_id": metadata['Metadata']['x-amz-meta-organization_id'], 
                    "creator_id": metadata['Metadata']['x-amz-meta-creator_id'], 
                    "workspace_id": metadata['Metadata']['x-amz-meta-workspace_id'],
                    "filepath": metadata['Metadata']['x-amz-meta-file_path'],
                    "codebase_name": metadata['Metadata']['x-amz-meta-codebase_name']
                }, token_json['access_token'])


def exec_onboarding_service(event, token):
    with httpx.Client(base_url=settings.API_URL, follow_redirects=True) as driverClient:
        payload = {**event}
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        print(json.dumps(payload))
        response = driverClient.post("/onboarding/", headers=headers, data=json.dumps(payload))

        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        event_response = response.json()
        print(event_response)
        # Make sure event was received successfully
        return "OK"
