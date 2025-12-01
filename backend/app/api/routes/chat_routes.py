from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...utils.langgraph_state import ChatState
from ...schemas.chat import ChatRequest, ChatResponse, ChatMessage
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


@router.post("/router", response_model=ChatResponse)
async def route_chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ChatResponse:
    if not hasattr(request.app.state, "router_graph"):
        raise HTTPException(status_code=500, detail="Router graph not initialized")

    router_graph = request.app.state.router_graph

    messages = [m.model_dump() for m in payload.messages]
    messages.append({"role": "user", "content": payload.message})

    user_type = payload.user_type or ("candidate" if getattr(current_user, "role", None) == "candidate" else "job_poster")
    state = ChatState(
        messages=messages,
        user_id=str(current_user.id),
        user_type=user_type,  # type: ignore[arg-type]
        qna_tree_id=payload.qna_tree_id,
        qna_mode=False,
        current_question_id=None,
    )
    state.metadata["db"] = db
    state.metadata["current_user"] = current_user

    result_state: ChatState = await router_graph.ainvoke(state)

    return ChatResponse(
        messages=[ChatMessage(**m) for m in result_state.messages],
        qna_mode=result_state.qna_mode,
        current_question_id=result_state.current_question_id,
        qna_tree_id=result_state.qna_tree_id,
        metadata=result_state.metadata,
    )
