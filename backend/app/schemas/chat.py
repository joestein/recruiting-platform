from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="Latest user message content.")
    messages: List[ChatMessage] = Field(default_factory=list, description="Existing conversation history.")
    user_type: Optional[str] = Field(None, description="candidate or job_poster; defaults from user role.")
    qna_tree_id: Optional[str] = None


class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    qna_mode: bool
    current_question_id: Optional[str]
    qna_tree_id: Optional[str]
    metadata: dict = Field(default_factory=dict)
