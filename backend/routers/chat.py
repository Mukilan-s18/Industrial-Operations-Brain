import time
import json
import asyncio
import uuid
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from backend.settings import settings
from backend.src.fallback import get_fallback
import redis.asyncio as redis
from backend.dependencies import (
    rca_graph,
    builder,
    CORPUS_COVERAGE_PCT,
    get_current_user,
)

router = APIRouter()

# Distributed Response Cache
redis_client = redis.from_url(settings.redis_uri, decode_responses=True)


class QueryRequest(BaseModel):
    query: str
    mode: str = "detailed"


class ActionRequest(BaseModel):
    thread_id: str


OPERATOR_RESTRICTED_TERMS = [
    "e-201",
    "electrical log",
    "engineer log",
    "moc",
    "management of change",
    "compliance report",
    "audit log",
    "rbac",
    "access control",
]


def check_role_access(role: str, query: str) -> tuple[bool, str]:
    if role.lower() == "operator":
        q_lower = query.lower()
        for term in OPERATOR_RESTRICTED_TERMS:
            if term in q_lower:
                return (
                    False,
                    f"Access denied: '{term}' is restricted to Engineer/Auditor roles.",
                )
    return True, ""


@router.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(
    request: Request, req: QueryRequest, current_user: dict = Depends(get_current_user)
):
    x_user_role = current_user["role"]
    start_time = time.time()
    query_lower = req.query.lower().strip()

    allowed, reason = check_role_access(x_user_role, req.query)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    if settings.use_fallback:
        fb = get_fallback(req.query)
        if fb:
            return {
                "answer": fb["answer"],
                "sources": fb["sources"],
                "contradiction_detected": fb["contradiction_detected"],
                "metrics": {
                    "latency_sec": round(time.time() - start_time, 4),
                    "faithfulness_score": 1.0,
                    "corpus_coverage_pct": CORPUS_COVERAGE_PCT,
                },
                "cached": True,
                "fallback": True,
            }

    cached_str = await redis_client.get(f"chat_cache:{query_lower}")
    if cached_str:
        cached = json.loads(cached_str)
        return {
            **cached,
            "metrics": {
                **cached["metrics"],
                "latency_sec": round(time.time() - start_time, 4),
            },
            "cached": True,
            "fallback": False,
        }

    inputs = {
        "original_query": req.query,
        "query": "",
        "graph_builder": builder,
        "user_role": x_user_role,
    }

    # Asynchronous invocation for high concurrency support
    # We must pass the config to LangGraph for memory saving (thread_id)
    thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await rca_graph.ainvoke(inputs, config=config)

    # Check if graph paused for HITL approval
    state_snapshot = rca_graph.get_state(config)
    requires_approval = (
        len(state_snapshot.next) > 0 and "execute_action" in state_snapshot.next
    )

    latency = round(time.time() - start_time, 2)

    response_data = {
        "answer": final_state.get("final_answer", ""),
        "sources": final_state.get("sources", []),
        "contradiction_detected": final_state.get("contradiction_detected", False),
        "contradiction_details": final_state.get("contradiction_details", ""),
        "abstained": final_state.get("abstained", False),
        "metrics": {
            "latency_sec": latency,
            "faithfulness_score": final_state.get("faithfulness_score", 0.0),
            "corpus_coverage_pct": CORPUS_COVERAGE_PCT,
        },
        "cached": False,
        "fallback": False,
        "action_taken": "PENDING_APPROVAL"
        if requires_approval
        else final_state.get("action_taken", "NONE"),
        "action_result": "Requires user approval to execute SAP transaction."
        if requires_approval
        else final_state.get("action_result", ""),
        "requires_approval": requires_approval,
        "thread_id": thread_id if requires_approval else None,
    }

    await redis_client.setex(
        f"chat_cache:{query_lower}",
        3600,  # Cache for 1 hour
        json.dumps(response_data),
    )
    return response_data


@router.post("/fallback/toggle")
async def toggle_fallback(enabled: bool):
    settings.use_fallback = enabled
    return {"fallback_mode": settings.use_fallback}


@router.post("/action/approve")
async def approve_action(
    req: ActionRequest, current_user: dict = Depends(get_current_user)
):
    """HITL: Resumes LangGraph execution to create the SAP Work Order."""
    config = {"configurable": {"thread_id": req.thread_id}}
    state_snapshot = rca_graph.get_state(config)

    if not state_snapshot.next:
        raise HTTPException(
            status_code=400, detail="No pending actions for this thread."
        )

    final_state = await rca_graph.ainvoke(None, config=config)
    return {
        "status": "Approved",
        "action_taken": final_state.get("action_taken"),
        "action_result": final_state.get("action_result"),
    }


@router.post("/action/reject")
async def reject_action(
    req: ActionRequest, current_user: dict = Depends(get_current_user)
):
    """HITL: Cancels the pending SAP action."""
    config = {"configurable": {"thread_id": req.thread_id}}
    state_snapshot = rca_graph.get_state(config)

    if not state_snapshot.next:
        raise HTTPException(
            status_code=400, detail="No pending actions for this thread."
        )

    # We update the state to bypass the action
    rca_graph.update_state(
        config,
        {"action_taken": "REJECTED", "action_result": "User rejected the action."},
    )

    return {"status": "Rejected", "message": "The pending SAP Work Order was canceled."}


@router.post("/stream")
@limiter.limit("10/minute")
async def stream_rca(
    request: Request, req: QueryRequest, current_user: dict = Depends(get_current_user)
):
    x_user_role = current_user["role"]
    allowed, reason = check_role_access(x_user_role, req.query)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    async def event_generator():
        start_time = time.time()
        inputs = {
            "original_query": req.query,
            "query": "",
            "graph_builder": builder,
            "user_role": x_user_role,
        }
        config = {"configurable": {"thread_id": "thread-1"}}

        # Asynchronous streaming
        async for output in rca_graph.astream(inputs, config=config):
            for node_name, state_update in output.items():
                event = {"node": node_name}
                if "status" in state_update:
                    event["status"] = state_update["status"]
                if "final_answer" in state_update:
                    event["answer"] = state_update["final_answer"]
                    event["contradiction_detected"] = state_update.get(
                        "contradiction_detected", False
                    )
                    event["faithfulness_score"] = state_update.get(
                        "faithfulness_score", 0.0
                    )
                    event["sources"] = state_update.get("sources", [])
                    event["latency_sec"] = round(time.time() - start_time, 2)
                if "action_taken" in state_update:
                    event["action_taken"] = state_update["action_taken"]
                    event["action_result"] = state_update.get("action_result", "")
                yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cache/clear")
async def clear_cache():
    # Only clear chat cache keys to avoid affecting celery tasks
    async for key in redis_client.scan_iter("chat_cache:*"):
        await redis_client.delete(key)
    return {"status": "Cache cleared"}
