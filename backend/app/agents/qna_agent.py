from __future__ import annotations

import re
import threading
from typing import Any, Dict, List, Optional

from instructor import from_openai
from openai import OpenAI

from ..core.config import get_settings
from ..qna_graph.models import HasTraitEdge, ProgrammingLanguagePreference, QuestionNode
from ..qna_graph.service import QnaService
from ..utils.langgraph_state import ChatState

settings = get_settings()

_openai_client: OpenAI | None = None
_openai_client_lock = threading.Lock()


def _get_openai_client() -> OpenAI:
    """Return a thread-safe singleton OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        with _openai_client_lock:
            if _openai_client is None:
                _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def _heuristic_classify_language(answer: str) -> ProgrammingLanguagePreference:
    lower = answer.lower()
    polyglot_patterns = [
        "depends",
        "no favorite",
        "whatever",
        "whatever the problem is",
        "depends on the problem",
        "polyglot",
    ]
    for pat in polyglot_patterns:
        if pat in lower:
            return ProgrammingLanguagePreference(kind="polyglot", language_name=None)
    # simple language match
    langs = ["python", "java", "go", "rust", "typescript", "javascript", "c++", "c#", "ruby"]
    for lang in langs:
        if lang in lower:
            return ProgrammingLanguagePreference(kind="single_language", language_name=lang)
    return ProgrammingLanguagePreference(kind="unknown", language_name=None)


def classify_with_instructor(question: QuestionNode, answer_text: str) -> tuple[str | None, Dict[str, Any], float]:
    classifier_cfg = question.classifier or {}
    strategy = classifier_cfg.get("strategy")
    dataclass_name = classifier_cfg.get("dataclass")
    if strategy == "instructor_dataclass" and dataclass_name == "ProgrammingLanguagePreference":
        if not settings.OPENAI_API_KEY:
            pref = _heuristic_classify_language(answer_text)
        else:
            client = _get_openai_client()
            inst_client = from_openai(client)
            pref = inst_client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[{"role": "user", "content": answer_text}],
                response_model=ProgrammingLanguagePreference,
            )
        normalized = None
        attributes: Dict[str, Any] = {"kind": pref.kind}
        if pref.kind == "polyglot":
            normalized = "polyglot"
        elif pref.kind == "single_language" and pref.language_name:
            normalized = _slugify(pref.language_name)
            attributes["language_name"] = pref.language_name
        else:
            normalized = "unknown"
        confidence = 0.9 if normalized != "unknown" else 0.5
        return normalized, attributes, confidence

    # Fallback
    pref = _heuristic_classify_language(answer_text)
    normalized = "polyglot" if pref.kind == "polyglot" else _slugify(pref.language_name or "unknown")
    confidence = 0.6
    return normalized, {"kind": pref.kind, "language_name": pref.language_name}, confidence


def _build_traits(user_id: str, question: QuestionNode, normalized_value: str, attributes: Dict[str, Any], confidence: float) -> List[HasTraitEdge]:
    attribute = question.attribute or (question.id if question else "unknown_attribute")
    concept_type = attribute
    concept_key = normalized_value or "unknown"
    return [
        HasTraitEdge(
            user_id=user_id,
            concept_type=concept_type,
            concept_key=concept_key,
            attribute=attribute,
            strength=1.0,
            confidence=confidence,
            normalized_value=normalized_value or "unknown",
        )
    ]


def _append_message(state: ChatState, role: str, content: str) -> None:
    state.messages.append({"role": role, "content": content})


def _summarize_history(messages: list[dict[str, str]], limit: int = 8) -> str:
    snippet = []
    for m in messages[-limit:]:
        snippet.append(f"{m.get('role')}: {m.get('content')}")
    return "\n".join(snippet)


def _generate_question_text(question: QuestionNode, state: ChatState) -> str:
    """
    If a generation_prompt is provided on the question node, use the LLM to craft
    a contextual question based on conversation history. Falls back to static text.
    """
    if not question.generation_prompt:
        return question.text
    if not settings.OPENAI_API_KEY:
        return question.text
    try:
        client = _get_openai_client()
        history = _summarize_history(state.messages)
        messages = [
            {"role": "system", "content": question.generation_prompt},
            {
                "role": "user",
                "content": f"Conversation history:\n{history}\n\nReturn one concise follow-up question.",
            },
        ]
        resp = client.chat.completions.create(model=settings.OPENAI_CHAT_MODEL, messages=messages, max_tokens=100)
        content = resp.choices[0].message.content if resp and resp.choices else None
        return content.strip() if content else question.text
    except Exception:
        return question.text


def ask_next_question(qna_service: QnaService):
    async def _ask(state: ChatState) -> ChatState:
        next_q = await qna_service.get_next_question_for_user(state.user_id, state.qna_tree_id or "")
        if not next_q:
            state.qna_mode = False
            state.current_question_id = None
            return state
        state.qna_mode = True
        state.current_question_id = next_q.id
        question_text = _generate_question_text(next_q, state)
        _append_message(state, "assistant", question_text)
        state.pending_attribute = next_q.attribute
        return state

    return _ask


def process_answer(qna_service: QnaService):
    async def _process(state: ChatState) -> ChatState:
        if not state.current_question_id:
            return state
        # latest human message
        latest_user = next((m for m in reversed(state.messages) if m.get("role") == "user"), None)
        if not latest_user:
            return state
        answer_text = latest_user.get("content", "")
        tree = qna_service.get_tree(state.qna_tree_id or "")
        if not tree:
            state.qna_mode = False
            return state
        question = tree.questions.get(state.current_question_id)
        if not question:
            state.qna_mode = False
            return state

        normalized_value = None
        attributes: Dict[str, Any] = {}
        confidence = 0.5

        if question.qtype == "free_text_classified":
            normalized_value, attributes, confidence = classify_with_instructor(question, answer_text)
        else:
            normalized_value = answer_text.strip().lower()
            attributes = {"value": normalized_value}
            confidence = 0.4

        traits = _build_traits(state.user_id, question, normalized_value or "unknown", attributes, confidence)
        # Best-effort graph persistence; continue Q&A even if graph errors.
        try:
            await qna_service.record_answer(
                user_id=state.user_id,
                question=question,
                raw_text=answer_text,
                normalized_value=normalized_value,
                attributes=attributes,
                confidence=confidence,
                traits=traits,
            )
        except Exception:
            pass

        state.traits.setdefault(question.attribute or question.id, []).append(
            {"normalized_value": normalized_value, "attributes": attributes, "confidence": confidence}
        )

        # Decide next question using in-memory tree follow-ups to avoid graph lookups blocking the flow.
        follow = question.follow_ups or {}
        next_id = follow.get(normalized_value) or follow.get("default")
        next_q = tree.questions.get(next_id) if next_id else None
        if next_q:
            state.current_question_id = next_q.id
            state.qna_mode = True
            question_text = _generate_question_text(next_q, state)
            _append_message(state, "assistant", question_text)
        else:
            state.qna_mode = False
            state.current_question_id = None
        return state

    return _process
