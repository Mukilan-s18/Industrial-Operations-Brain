from fastapi import APIRouter, Depends, Query
from backend.dependencies import builder, ner, get_current_user

router = APIRouter()


@router.get("/api/compliance-gaps")
def get_compliance_gaps(
    date: str = None, current_user: dict = Depends(get_current_user)
):
    role = current_user["role"]
    if role and "operator" in role.lower():
        return []
    return builder.get_compliance_gaps(date)


@router.get("/api/ner-evaluation")
def get_ner_evaluation():
    return ner.evaluate_accuracy()


@router.get("/api/failure-patterns")
def get_failure_patterns():
    return builder.get_failure_patterns()
