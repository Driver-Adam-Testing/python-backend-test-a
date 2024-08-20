# from uuid import UUID
#
# from fastapi.testclient import TestClient
# from sqlmodel import Session
#
# from app.core.config import settings
#
# # from app.tests.utils.item import create_random_item
#
# from app.tests.utils.auth import get_auth0_token
#
#
# def test_create_document(
#         client: TestClient
# ) -> None:
#     #TODO create a workspace and codebase
#
#     # data = {"workspace_id": str(uuid.uuid4()), "codebase_id": str(uuid.uuid4())}
#     workspace_id = "90c28b84-39f9-4bd8-b7cc-6a97ef530468"
#     codebase_id = "cd7bf15b-ebdd-4882-96a0-df766a62227f"
#     data = {"workspace_id": workspace_id, "codebase_id": codebase_id}
#     token = get_auth0_token()
#     print(token)
#
#     response = client.post(
#         f"{settings.API_V1_STR}/content/document",
#         headers={
#             "Authorization": f"Bearer {token}",
#             "X-Forwarded-For": "testing"
#         },
#         json=data,
#     )
#     assert response.status_code == 200
#     content = response.json()
#
#     # Check if content_id is a valid UUID
#     try:
#         UUID(content["content_id"])
#     except ValueError:
#         assert False, "content_id is not a valid UUID"
