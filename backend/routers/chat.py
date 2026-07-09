import time
import json
import asyncio
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.settings import settings
from backend.src.fallback import get_fallback
from backend.dependencies import rca_graph, builder, CORPUS_COVERAGE_PCT

router = APIRouter()

# Dynamic Response Cache
RESPONSE_CACHE: dict[str, dict] = {}


class QueryRequest(BaseModel):
    query: str
    mode: str = "detailed"


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
async def chat_endpoint(
    req: QueryRequest, x_user_role: str = Header(default="operator")
):
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

    if query_lower in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[query_lower]
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
    config = {"configurable": {"thread_id": "thread-1"}}
    final_state = await rca_graph.ainvoke(inputs, config=config)

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
        "action_taken": final_state.get("action_taken", "NONE"),
        "action_result": final_state.get("action_result", ""),
    }

    RESPONSE_CACHE[query_lower] = response_data
    return response_data


@router.post("/fallback/toggle")
async def toggle_fallback(enabled: bool):
    settings.use_fallback = enabled
    return {"fallback_mode": settings.use_fallback}


@router.post("/stream")
async def stream_rca(req: QueryRequest, x_user_role: str = Header(default="operator")):
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
                yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/cache/clear")
async def clear_cache():
    RESPONSE_CACHE.clear()
    return {"status": "Cache cleared"}
