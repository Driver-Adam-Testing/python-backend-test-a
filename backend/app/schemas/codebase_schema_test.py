import pytest
from app.schemas.codebase_schema import CodebaseAnalysisMetrics
from pydantic import ValidationError


@pytest.fixture
def modal_function_call_response() -> dict:
    return {
        "analyzable_bytes": 750,
        "analyzable_files": 75,
        "total_bytes": 1000,
        "total_files": 100,
        "analyzable_files_by_extension": {
            ".h": 25,
            ".c": 25,
            ".cpp": 25,
        },
        "analyzable_files_by_type": {
            "Header": 25,
            "C": 25,
            "C++": 25,
        },
        "analyzable_bytes_by_extension": {
            ".h": 250,
            ".c": 250,
            ".cpp": 250,
        },
        "analyzable_bytes_by_type": {
            "Header": 250,
            "C": 250,
            "C++": 250,
        },
    }


def test_codebase_analysis_metrics(modal_function_call_response: dict) -> None:
    codebase_analysis_metrics = CodebaseAnalysisMetrics(**modal_function_call_response)
    assert codebase_analysis_metrics.analyzable_bytes == 750
    assert codebase_analysis_metrics.analyzable_files == 75
    assert codebase_analysis_metrics.total_bytes == 1000
    assert codebase_analysis_metrics.total_files == 100
    assert codebase_analysis_metrics.analyzable_files_by_extension == {
        ".h": 25,
        ".c": 25,
        ".cpp": 25,
    }
    assert codebase_analysis_metrics.analyzable_files_by_type == {
        "Header": 25,
        "C": 25,
        "C++": 25,
    }
    assert codebase_analysis_metrics.analyzable_bytes_by_extension == {
        ".h": 250,
        ".c": 250,
        ".cpp": 250,
    }
    assert codebase_analysis_metrics.analyzable_bytes_by_type == {
        "Header": 250,
        "C": 250,
        "C++": 250,
    }
    assert codebase_analysis_metrics.analyzable_sloc == 15
    assert codebase_analysis_metrics.total_sloc == 20
    assert codebase_analysis_metrics.analyzable_sloc_by_extension == {
        ".h": 5,
        ".c": 5,
        ".cpp": 5,
    }
    assert codebase_analysis_metrics.analyzable_sloc_by_type == {
        "Header": 5,
        "C": 5,
        "C++": 5,
    }


def test_codebase_analysis_metrics_immutability(
    modal_function_call_response: dict,
) -> None:
    codebase_analysis_metrics = CodebaseAnalysisMetrics(**modal_function_call_response)
    with pytest.raises(ValidationError):
        codebase_analysis_metrics.analyzable_bytes = 0
    with pytest.raises(ValidationError):
        codebase_analysis_metrics.analyzable_sloc = 0
    assert codebase_analysis_metrics.analyzable_bytes == 750
    assert codebase_analysis_metrics.analyzable_sloc == 15
