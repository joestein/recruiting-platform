from __future__ import annotations

from typing import Callable

from langgraph.graph import END, StateGraph

from ..qna_graph.service import QnaService
from ..utils.langgraph_state import ChatState
from . import calendar_agent_stub, general_chat_agent, qna_agent


RouteKey = str


def build_router_graph(qna_service: QnaService) -> Callable[[ChatState], ChatState]:
    graph = StateGraph(ChatState)

    async def route_message(state: ChatState) -> ChatState:
        last_user = next((m for m in reversed(state.messages) if m.get("role") == "user"), None)
        text = (last_user or {}).get("content", "").lower()

        # Simple scheduling intent detection
        scheduling_keywords = ["schedule", "availability", "available", "book", "calendar", "meet"]
        if any(k in text for k in scheduling_keywords):
            state.metadata["route_decision"] = "calendar"
            return state

        if state.qna_mode:
            # If we are mid-Q&A and have a current question, process answer
            if state.current_question_id:
                state.metadata["route_decision"] = "process_answer"
                return state
            state.metadata["route_decision"] = "ask_next_question"
            return state

        # Kick off onboarding flow if none exists and user is a candidate
        if state.user_type == "candidate" and not state.qna_tree_id:
            state.qna_tree_id = "candidate.programming_language"
            state.qna_mode = True
            state.metadata["route_decision"] = "ask_next_question"
            return state

        state.metadata["route_decision"] = "general"
        return state

    # Nodes
    graph.add_node("route_message", route_message)
    graph.add_node("ask_next_question", qna_agent.ask_next_question(qna_service))
    graph.add_node("process_answer", qna_agent.process_answer(qna_service))
    graph.add_node("general_chat", general_chat_agent.general_chat())
    graph.add_node("calendar_agent", calendar_agent_stub.handle_calendar_intent())

    graph.set_entry_point("route_message")

    def route_selector(state: ChatState) -> RouteKey:
        return state.metadata.get("route_decision", "general")

    graph.add_conditional_edges(
        "route_message",
        route_selector,
        {
            "ask_next_question": "ask_next_question",
            "process_answer": "process_answer",
            "general": "general_chat",
            "calendar": "calendar_agent",
            "__default__": "general_chat",
        },
    )

    # End nodes after each operation to return control to caller
    for node in ["ask_next_question", "process_answer", "general_chat", "calendar_agent"]:
        graph.add_edge(node, END)

    return graph.compile()
