from fastapi import APIRouter, Query
from backend.dependencies import builder, ner

router = APIRouter()


@router.get("/api/compliance-gaps")
def get_compliance_gaps(
    date: str = None, role: str = Query(None, description="User Role")
):
    if role and "Operator" in role:
        return []
    return builder.get_compliance_gaps(date)


@router.get("/api/ner-evaluation")
def get_ner_evaluation():
    return ner.evaluate_accuracy()


@router.get("/api/failure-patterns")
def get_failure_patterns():
    return builder.get_failure_patterns()
