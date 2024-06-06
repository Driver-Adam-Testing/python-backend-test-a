import os

import boto3
from botocore.exceptions import NoCredentialsError
from database.config import settings
from database.models_v1 import (
    Chunk,
    Codebase,
    ContentMetadata,
    DerivedContent,
    DerivedContentType,
    Llm,
    SourceContent,
    SourceContentType,
    Workspace,
)
from sqlalchemy import create_engine
from sqlmodel import Session, select

# Define the source and target database URLs
source_database_url = os.getenv("SOURCE_DATABASE_URL")
target_database_url = str(settings.SQLALCHEMY_DATABASE_URI)
print(f"migrating \n\n{source_database_url}  \n\nto \n\n{target_database_url}\n\n")

# Create engines for source and target databases
source_engine = create_engine(source_database_url)
target_engine = create_engine(target_database_url)

# List of all models
models = [
    Workspace,
    Codebase,
    DerivedContentType,
    SourceContentType,
    Llm,
    DerivedContent,
    SourceContent,
    ContentMetadata,
    Chunk,
]


for model in models:
    with Session(source_engine) as source_session:
        # Query all records from the source database
        records = source_session.exec(select(model)).all()
        print(f"Migrating {len(records)} records of type {model}")

        # Check if records are being fetched
        if not records:
            print(f"No records found for {model}")
            continue

        # Iterate over each record
        try:
            for record in records:
                # Create a new record with the same attributes as the source record
                new_record = model(**record.__dict__)

                with Session(target_engine) as target_session:
                    target_session.add(new_record)
                    target_session.commit()
            print(
                f"Successfully committed {len(records)} records to the target database."
            )
        except Exception as e:
            print(f"Error during migration of records for {model}: {e}")


# Configure source S3 details
source_s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# Configure target S3 details for local development
target_s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",  # LocalStack default endpoint
    aws_access_key_id="test",  # Default LocalStack credentials
    aws_secret_access_key="test",  # Default LocalStack credentials
    region_name="us-east-1",  # Default region for LocalStack
)
try:
    print("Starting to list all buckets in source S3.")
    source_buckets = source_s3.list_buckets()
    if "Buckets" in source_buckets:
        for bucket in source_buckets["Buckets"]:
            source_bucket_name = bucket["Name"]
            target_bucket_name = (
                source_bucket_name  # Assuming target bucket name is the same as source
            )
            print(f"Processing bucket: {source_bucket_name}")

            # Check if the target bucket exists, skip if it does
            try:
                target_s3.head_bucket(Bucket=target_bucket_name)
                print(
                    f"Bucket {target_bucket_name} already exists in target, skipping."
                )
                continue
            except target_s3.exceptions.ClientError:
                print(
                    f"Bucket {target_bucket_name} does not exist in target, proceeding with copy."
                )
                target_s3.create_bucket(Bucket=target_bucket_name)
                print(f"Created bucket {target_bucket_name} in target.")
            # List all objects in the current source bucket
            print(f"Listing objects in source bucket: {source_bucket_name}")
            source_objects = source_s3.list_objects_v2(Bucket=source_bucket_name)
            if "Contents" in source_objects:
                for obj in source_objects["Contents"]:
                    copy_source = {"Bucket": source_bucket_name, "Key": obj["Key"]}

                    # Check if the object exists in the target bucket, skip if it does
                    try:
                        target_s3.head_object(Bucket=target_bucket_name, Key=obj["Key"])
                        print(
                            f"Object {obj['Key']} already exists in {target_bucket_name}, skipping."
                        )
                        continue
                    except target_s3.exceptions.ClientError:
                        print(
                            f"Copying {obj['Key']} from {source_bucket_name} to {target_bucket_name}"
                        )
                    # Copy the object from source to target
                    object_content = source_s3.get_object(
                        Bucket=source_bucket_name, Key=obj["Key"]
                    )["Body"].read()
                    target_s3.put_object(
                        Bucket=target_bucket_name, Key=obj["Key"], Body=object_content
                    )
    print("Operation completed successfully for all buckets.")
except NoCredentialsError:
    print("Credentials not available for AWS S3.")
