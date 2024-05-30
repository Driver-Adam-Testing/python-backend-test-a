import json
import os
from hashlib import sha256

import jwt
import requests  # type: ignore
import strawberry

from app.core.logger import logger


@strawberry.type
class ComprehenderResponse:
    status_text: str
    status: str
    message: str
    data: dict | None


@strawberry.input
class ExecuteComprehenderRequestInput:
    endpoint: str
    input: dict
    context: dict | None = None


@strawberry.input
class ExecuteCreateEmbeddingsInput:
    codebase_id: str
    workspace_id: str
    context: dict


def create_signature(input: dict, secret_key: str) -> str:
    return sha256(secret_key.encode() + json.dumps(input).encode("utf-8")).hexdigest()


def execute_comprehender_request(
    input: ExecuteComprehenderRequestInput,
) -> ComprehenderResponse:
    logger.info(f"[ExecuteComprehenderRequest]:{json.dumps(input.input, indent=2)}")
    url = f"{os.environ['COMPREHENDER_API_URL']}{input.endpoint}"
    secret_key = os.environ["COMPREHENDER_API_SECRET"]
    token = jwt.encode({}, secret_key, algorithm="HS256")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = input.input
    if input.context is not None:
        body["echoed_context"] = {
            **input.context,
            "prompt_signature": create_signature(input.input, secret_key),
        }
    try:
        response = requests.post(url, json=body, headers=headers)
        return ComprehenderResponse(
            status_text="success",
            status=str(response.status_code),
            message="Request successful",
            data=response.json(),
        )
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return ComprehenderResponse(
            status_text="failed", status="500", message=str(e), data=None
        )


def execute_create_embeddings(
    input: ExecuteCreateEmbeddingsInput,
) -> ComprehenderResponse:
    logger.info(
        f"[ExecuteCreateEmbeddings]:{json.dumps({'workspace_id': input.workspace_id, 'codebase_id': input.codebase_id}, indent=2)}"
    )
    url = f"{os.environ['COMPREHENDER_API_URL']}/create_embeddings"
    secret_key = os.environ["COMPREHENDER_API_SECRET"]
    token = jwt.encode({}, secret_key, algorithm="HS256")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "workspace_id": input.workspace_id,
        "codebase_id": input.codebase_id,
        "echoed_context": input.context,
    }
    try:
        response = requests.post(url, json=body, headers=headers)
        return ComprehenderResponse(
            status_text="success",
            status=str(response.status_code),
            message="Request successful",
            data=response.json(),
        )
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return ComprehenderResponse(
            status_text="failed", status="500", message=str(e), data=None
        )


def poll_comprehender_request(call_id: str) -> ComprehenderResponse:
    url = f"{os.environ['COMPREHENDER_API_URL']}/{call_id}"
    secret_key = os.environ["COMPREHENDER_API_SECRET"]
    token = jwt.encode({}, secret_key, algorithm="HS256")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(url, headers=headers)
        return ComprehenderResponse(
            status_text="success",
            status=str(response.status_code),
            message="Polling successful",
            data=response.json(),
        )
    except requests.RequestException as e:
        logger.error(f"Polling failed: {str(e)}")
        return ComprehenderResponse(
            status_text="failed", status="500", message=str(e), data=None
        )
