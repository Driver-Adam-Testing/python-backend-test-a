# Driver Data

This container copies database and S3 records for a given organization + codebase ID to a destination.

Currently, this only works with localhost as a target due to AWS cross-account permissions issues when copying S3 files. Whether or not we even _should_ move data between environments is an additional consideration.

## Example (java-sample)

```
poetry install --no-root
poetry run python copy_data.py --org-id org_s76pU1v8LAYhTOWB --codebase-id fafab059-afe8-47b8-b195-2cbef2d58c6a
```

## Example .env configuration (update accordingly)

```
LOG_LEVEL=DEBUG

AWS_REGION=us-east-1

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin


SRC_AWS_ACCESS_KEY_ID=dev_secrets_manager
SRC_AWS_SECRET_ACCESS_KEY=dev_secrets_manager
SOURCE_DATABASE_URL=dev_url_in_1pass

TARGET_AWS_ACCESS_KEY_ID=minioadmin
TARGET_AWS_SECRET_ACCESS_KEY=minioadmin
TARGET_AWS_S3_ENDPOINT_URL=http://localhost:9000
TARGET_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/postgres
```
