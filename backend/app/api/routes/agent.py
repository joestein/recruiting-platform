from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...models.user import User
from ...services.agent import run_agent_chat
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str
    mode: str = "recruiter_assistant"


class AgentChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reply_text = run_agent_chat(
        db=db,
        user=user,
        message=payload.message,
        mode=payload.mode,
    )
    return AgentChatResponse(reply=reply_text)
