import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from app.core.config import settings

region_name = "us-east-1"

def write_secret(secret_name, secret_value):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    )

    try:
        value = read_secret(secret_name)
        if value:
            print(f"Secret {secret_name} already exists. Updating the secret.")
            response = client.update_secret(SecretId=secret_name, SecretString=secret_value)
        else:
            print(f"Secret {secret_name} does not exist. Creating a new secret.")
            response = client.create_secret(Name=secret_name, SecretString=secret_value)
        return response
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None


def read_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    )
    try:
        response = client.get_secret_value(SecretId=secret_name)
        # Assuming the secret is stored as a string
        return response
    except NoCredentialsError:
        print("No credentials could be found")
    except PartialCredentialsError:
        print("Incomplete credentials found")
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None


def format_secret_key(org_id: str, user_id: str, provider: str):
    user_id = user_id.replace("|", "_")
    return f"DRIVER_AI_CUSTOMER/{provider}/{org_id}/{user_id}"
