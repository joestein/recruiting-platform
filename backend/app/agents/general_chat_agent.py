from __future__ import annotations

from ..services.agent import run_agent_chat
from ..utils.langgraph_state import ChatState


def general_chat():
    async def _chat(state: ChatState) -> ChatState:
        # Expect current_user and db in metadata
        user = state.metadata.get("current_user")
        db = state.metadata.get("db")
        if not user or db is None:
            reply = "I'm missing context to answer right now."
        else:
            latest_user = next((m for m in reversed(state.messages) if m.get("role") == "user"), None)
            message = latest_user.get("content") if latest_user else ""
            reply = run_agent_chat(db=db, user=user, message=message)

        state.messages.append({"role": "assistant", "content": reply})
        state.qna_mode = False
        state.current_question_id = None
        return state

    return _chat
