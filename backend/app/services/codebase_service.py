import json

from modal import Function
from modal.functions import FunctionCall

from app.core.config import settings
from app.schemas.codebase_schema import (
    CodebaseAnalysisMetrics,
    CodebaseAnalysisRequest,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
    ModalFunctionCallResponse,
)


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


class CodebaseService:
    @staticmethod
    def execute_codebase_analysis(
        request: CodebaseAnalysisRequest,
    ) -> CodebaseAnalysisResponse:
        modal_function = Function.lookup(
            "codebase-onboarding",
            "run_pre_codebase_analysis",
            environment_name=settings.MODAL_ENVIRONMENT,  # for some reason I get app not found without environment_name
        )
        instance = modal_function.spawn(request.download_url)
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
