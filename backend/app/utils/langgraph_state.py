from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ChatState:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_id: str = ""
    user_type: Literal["candidate", "job_poster"] = "candidate"
    qna_tree_id: Optional[str] = None
    current_question_id: Optional[str] = None
    qna_mode: bool = False
    pending_attribute: Optional[str] = None
    traits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
