# import pytest

# # Reuse fixtures from conftest.py
# from database.models_v1 import Workspace
# from fastapi import HTTPException
# from pydantic import ValidationError

# from app.schemas.upload_schema import UploadCodebaseRequest, UploadPDFRequest
# from app.services.upload_service import UploadService


# @pytest.fixture
# def upload_service(db):
#     return UploadService(db)


# @pytest.fixture
# def workspace(db, current_user_with_org):
#     workspace = Workspace(
#         display_name="Default",
#         organization_id=current_user_with_org.organization_id,
#     )
#     db.add(workspace)
#     db.commit()
#     return workspace


# VALID_CODEBASE_URL_PREFIX = (
#     "https://development-codebase-dropzone.s3.amazonaws.com/codebases/"
# )
# VALID_DOCUMENTS_URL_PREFIX = (
#     "https://development-codebase-dropzone.s3.amazonaws.com/documents/"
# )


# def test_upload_codebase_success(upload_service, current_user_with_org):
#     request = UploadCodebaseRequest(file_path="test_codebase.zip")
#     response = upload_service.upload_codebase(current_user_with_org, request)
#     assert response.upload_url.startswith(VALID_CODEBASE_URL_PREFIX)


# def test_upload_codebase_no_default_workspace(
#     upload_service, current_user_with_other_org
# ):
#     request = UploadCodebaseRequest(file_path="test_codebase.zip")

#     with pytest.raises(HTTPException):
#         upload_service.upload_codebase(current_user_with_other_org, request)


# def test_upload_codebase_invalid_file_path(upload_service, current_user_with_org):
#     with pytest.raises(ValidationError):
#         UploadCodebaseRequest(file_path="test_codebase.txt")


# def test_upload_pdf_success(upload_service, current_user_with_org):
#     request = UploadPDFRequest(file_path="test_codebase.pdf")
#     response = upload_service.upload_pdf(current_user_with_org, request)
#     assert response.upload_url.startswith(VALID_DOCUMENTS_URL_PREFIX)


# def test_upload_pdf_no_default_workspace(upload_service, current_user_with_other_org):
#     request = UploadPDFRequest(file_path="test_codebase.pdf")

#     with pytest.raises(HTTPException):
#         upload_service.upload_pdf(current_user_with_other_org, request)


# def test_upload_pdf_invalid_file_path(upload_service, current_user_with_org):
#     with pytest.raises(ValidationError):
#         UploadPDFRequest(file_path="test_codebase.zip")
