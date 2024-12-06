import json

from modal import Function
from modal.functions import FunctionCall

from app.core.config import settings
from app.schemas.codebase_schema import (
    CodebaseAnalysisMetrics,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
    ModalFunctionCallResponse,
)
from app.utils.aws_s3 import dropzone_bucket_name, org_id_to_hash, parse_presigned_url


def execute_modal_function_call(call_id: str) -> ModalFunctionCallResponse:
    function_call = FunctionCall.from_id(call_id)
    modal_response = ModalFunctionCallResponse(
        call_id=call_id,
        status="pending",
        response=None,
    )
    print(modal_response)
    try:
        response = function_call.get(timeout=0)
        modal_response.response = json.loads(response)
        modal_response.status = "completed"
    except TimeoutError:
        modal_response.status = "running"
    except Exception as e:
        modal_response.status = "error"
        modal_response.error = str(e)
    return modal_response


def validate_codebase_analysis_presigned_url(
    url: str, object_key_prefix: str, org_id: str
) -> bool:
    """
    Security check: Validate that the presigned URL is valid for codebase analysis.
    1. Check the bucket and object key prefix.
    2. Check that the org_id is part of the object key.
    """
    org_hash = org_id_to_hash(org_id)
    valid_bucket = dropzone_bucket_name()
    parsed_bucket, parsed_key = parse_presigned_url(url)
    object_key_parts = parsed_key.split("/")[:2]
    return parsed_bucket == valid_bucket and (
        org_hash in object_key_parts and object_key_prefix in object_key_parts
    )


class CodebaseAnalysisException(Exception):
    pass


class CodebaseService:
    @staticmethod
    def execute_codebase_analysis(
        organization_id: str,
        download_url: str,
    ) -> CodebaseAnalysisResponse:
        if not validate_codebase_analysis_presigned_url(
            download_url,
            "analysis",
            organization_id,
        ):
            raise CodebaseAnalysisException("Forbidden")

        modal_function = Function.lookup(
            "codebase-onboarding",
            "run_pre_codebase_analysis",
            environment_name=settings.MODAL_ENVIRONMENT,  # for some reason I get app not found without environment_name
        )
        instance = modal_function.spawn(download_url)
        return CodebaseAnalysisResponse(call_id=instance.object_id)

    @staticmethod
    def get_codebase_analysis_results(call_id: str) -> CodebaseAnalysisResult:
        modal_response = execute_modal_function_call(call_id)
        codebase_analysis_results = CodebaseAnalysisResult(
            call_id=call_id,
            status=modal_response.status,
            error=modal_response.error,
        )

        if modal_response.status == "completed":
            codebase_analysis_metrics = CodebaseAnalysisMetrics(
                **modal_response.response
            )
            print(codebase_analysis_metrics)
            codebase_analysis_results.result = codebase_analysis_metrics

        return codebase_analysis_results
