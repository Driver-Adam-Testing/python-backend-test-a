import pytest

from app.services.codebase_service import (
    CodebaseAnalysisAuthException,
    validate_analyzed_codebase_object_key,
    validate_codebase_analysis_presigned_url,
)


def test_validate_codebase_analysis_presigned_url() -> None:
    url = "https://development-codebase-dropzone.s3.amazonaws.com/analysis/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/foo.zip"

    validate_codebase_analysis_presigned_url(url, "analysis", "org_s76pU1v8LAYhTOWB")

    with pytest.raises(CodebaseAnalysisAuthException):
        validate_codebase_analysis_presigned_url(url, "analysis", "org_id")

    with pytest.raises(CodebaseAnalysisAuthException):
        validate_codebase_analysis_presigned_url(url, "key", "org_s76pU1v8LAYhTOWB")


def test_validate_analyzed_codebase_object_key() -> None:
    codebase_object_key = "analysis/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/foo.zip"
    bad_codebase_object_key = "analysis/other_org/foo.zip"

    validate_analyzed_codebase_object_key(codebase_object_key, "org_s76pU1v8LAYhTOWB")

    with pytest.raises(CodebaseAnalysisAuthException):
        validate_analyzed_codebase_object_key(codebase_object_key, "org_id")

    with pytest.raises(CodebaseAnalysisAuthException):
        validate_analyzed_codebase_object_key(
            bad_codebase_object_key, "org_s76pU1v8LAYhTOWB"
        )
