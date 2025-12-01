from __future__ import annotations

from ..utils.langgraph_state import ChatState


def handle_calendar_intent():
    async def _calendar(state: ChatState) -> ChatState:
        state.metadata["calendar_intent"] = True
        state.messages.append(
            {
                "role": "assistant",
                "content": "I noted you want to schedule something. A calendar agent will handle this soon. "
                "For now, please share a few available times.",
            }
        )
        return state

    return _calendar
