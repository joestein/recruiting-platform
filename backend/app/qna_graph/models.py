from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass
class Concept:
    id: Optional[str] = None
    type: str = ""
    key: str = ""
    label: Optional[str] = None
    status: Literal["canonical", "unknown", "candidate"] = "canonical"
    embedding: Optional[List[float]] = None


@dataclass
class QuestionNode:
    id: str = ""
    user_type: Literal["candidate", "job_poster"] = "candidate"
    text: str = ""
    attribute: Optional[str] = None
    qtype: Literal["free_text_classified", "free_text", "single_choice"] = "free_text"
    classifier: Optional[Dict[str, Any]] = None
    options: List[Dict[str, Any]] = field(default_factory=list)
    follow_ups: Dict[str, str] = field(default_factory=dict)
    end_of_tree: bool = False


@dataclass
class AnswerRecord:
    user_id: str
    question_id: str
    raw_text: str
    normalized_value: Optional[str]
    attributes: Dict[str, Any]
    confidence: float
    timestamp: datetime
    source: str = "qa_tree"


@dataclass
class QTreeDefinition:
    version: int
    namespace: str
    user_type: str
    tree_id: str
    root_question_id: str
    questions: Dict[str, QuestionNode]


@dataclass
class HasTraitEdge:
    user_id: str
    concept_type: str
    concept_key: str
    attribute: str
    strength: float
    confidence: float
    normalized_value: str


@dataclass
class RequiresSkillEdge:
    job_id: str
    concept_type: str
    concept_key: str
    attribute: str
    weight: float
    required: bool


# Example classifier dataclass for Instructor
@dataclass
class ProgrammingLanguagePreference:
    kind: Literal["polyglot", "single_language", "unknown"]
    language_name: Optional[str] = None
