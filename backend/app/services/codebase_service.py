import json
from pathlib import Path

from modal import Function
from modal.functions import FunctionCall

from app.core.config import settings
from app.core.logger import logger
from app.schemas.codebase_schema import (
    CodebaseAnalysisMetrics,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
    ModalFunctionCallResponse,
)
from app.utils.aws_s3 import (
    copy_s3_object,
    dropzone_bucket_name,
    org_id_to_hash,
    parse_presigned_url,
)


class CodebaseAnalysisAuthException(Exception):
    pass


def execute_modal_function_call(call_id: str) -> ModalFunctionCallResponse:
    function_call = FunctionCall.from_id(call_id)
    modal_response = ModalFunctionCallResponse(
        call_id=call_id,
        status="pending",
        response=None,
    )
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
) -> None:
    """
    Security check: Validate that the presigned URL is valid for codebase analysis.
    1. Check the bucket and object key prefix.
    2. Check that the org_id is part of the object key.
    """
    org_hash = org_id_to_hash(org_id)
    valid_bucket = dropzone_bucket_name()
    parsed_bucket, parsed_key = parse_presigned_url(url)
    object_key_parts = parsed_key.split("/")[:2]
    if not (
        parsed_bucket == valid_bucket
        and (org_hash in object_key_parts and object_key_prefix in object_key_parts)
    ):
        raise CodebaseAnalysisAuthException("Forbidden")


def validate_analyzed_codebase_object_key(
    codebase_object_key: str, org_id: str
) -> None:
    """
    Security check: Validate that the object key is valid for analyzed codebase.
    """
    org_hash = org_id_to_hash(org_id)
    object_key_parts = codebase_object_key.split("/")[:2]
    object_key_prefix = "analysis"
    if org_hash not in object_key_parts and object_key_prefix in object_key_parts:
        raise CodebaseAnalysisAuthException("Forbidden")


class CodebaseService:
    @staticmethod
    def execute_codebase_analysis(
        organization_id: str,
        download_url: str,
    ) -> CodebaseAnalysisResponse:
        validate_codebase_analysis_presigned_url(
            download_url,
            "analysis",
            organization_id,
        )  # validate the presigned URL before spawning the modal function to prevent unauthorized access

        modal_function = Function.lookup(
            "inspector-v2",
            "run_pre_codebase_analysis",
            environment_name=settings.MODAL_ENVIRONMENT,  # for some reason I get app not found without environment_name
        )
        _, codebase_object_key = parse_presigned_url(download_url)
        instance = modal_function.spawn(download_url)
        return CodebaseAnalysisResponse(
            call_id=instance.object_id,
            codebase_object_key=codebase_object_key,  # S3 object key for the codebase to be used if and when customer triggers onboarding
        )

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
            # print(codebase_analysis_metrics)
            codebase_analysis_results.result = codebase_analysis_metrics

        return codebase_analysis_results

    @staticmethod
    def trigger_codebase_onboarding(
        organization_id: str,
        codebase_object_key: str,
    ) -> None:
        validate_analyzed_codebase_object_key(
            codebase_object_key,
            organization_id,
        )  # validate the object key before triggering the onboarding to prevent unauthorized access

        logger.info("Triggering codebase onboarding...")
        # we can trigger the codebase onboarding by moving the analyzed codebase to the codebase folder in the dropzone bucket
        bucket_name = dropzone_bucket_name()
        real_file_name = Path(codebase_object_key).name
        destination_real_object_key = (
            f"codebases/{org_id_to_hash(organization_id)}/{real_file_name}"
        )

        copy_s3_object(
            source_bucket=bucket_name,
            source_key=codebase_object_key,
            dest_bucket=bucket_name,
            dest_key=destination_real_object_key,
        )  # copy the analyzed codebase to the codebase folder

        logger.info(
            f"Codebase onboarding triggered for {real_file_name} in {organization_id}"
        )
