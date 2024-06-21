import json
import httpx
import botocore 
import botocore.session 
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig 
from config import settings

# Ensure you have the necessary permissions in your Lambda's execution role to read from S3 and SNS
# TODO: this service receives events from s3 when objects are uploaded
# 1. It should be able to handle the event
# 2. It should be able to parse the event
# 3. It should be able to extract the object key
# 4. It should be able to execute an api call to run the onboarding service

async def handler(event, context):
    # Parse the SNS message
    for record in event['Records']:
        sns_message = json.loads(record['Sns']['Message'])

        sm_client = botocore.session.get_session().create_client('secretsmanager')
        cache_config = SecretCacheConfig()
        cache = SecretCache(config = cache_config, client = sm_client)

        s3_client = botocore.session.get_session().create_client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
            if settings.AWS_S3_ENDPOINT_URL
            else None,
        )

        client_id = cache.get_secret_string(settings.CLIENT_ID_SECRET) if settings.ENVIRONMENT != "local" else settings.CLIENT_ID_SECRET
        client_secret = cache.get_secret_string(settings.CLIENT_SECRET_SECRET) if settings.ENVIRONMENT != "local" else settings.CLIENT_SECRET_SECRET
        payload = json.dumps({"client_id":client_id,"client_secret":client_secret,"audience":settings.API_URL,"grant_type":"client_credentials"})
        
        async with httpx.AsyncClient(base_url=settings.AUTH0_URL) as auth0Client:
            # Fetch one M2M token per invocation of the lambda. This could be cached but would require additional impl similar to SecretCache above
            token_response = await auth0Client.post("/oauth/token", headers={ 'content-type': "application/json" }, data=payload)
            token_response.raise_for_status() # Raises an exception for 4XX/5XX responses
            token_json = token_response.json()

            # Extract information from the S3 event
            for s3_record in sns_message['Records']:
                print(s3_record)
                bucket_name = s3_record['s3']['bucket']['name']
                object_key = s3_record['s3']['object']['key']
                
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": object_key},
                    ExpiresIn=3600,
                )

                # Execute API call to run the onboarding service
                # PresignedURL to download archive
                # Name of archive
                # OrgId
                # Creator ID
                # Workspace
                return await exec_onboarding_service({ "download_url": presigned_url, "object_key": object_key, "org_id": "TODO", "creator_id": "TODO", "workspace_id": "TODO", s3_record: s3_record }, token_json['access_token'])


async def exec_onboarding_service(event, token):
    async with httpx.AsyncClient(base_url=settings.API_URL) as driverClient:
        payload = {**event}
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        response = await driverClient.post("/onboarding", headers=headers, data=json.dumps(payload))

        # For Endpoint
        # onboard_and_inspect = modal.Function.lookup("codebase-onboarding", "onboard_and_inspect")
        # onboard_and_inspect.remote(dropzone_bucket_name, archive_name, org_id, creator_id, workspace_id)
        response.raise_for_status()  # Raises an exception for 4XX/5XX responses
        event_response = response.json()
        print(event_response)
        # Make sure event was received successfully
        return "OK"
