from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .models import QTreeDefinition, QuestionNode


class QTreeValidationError(ValueError):
    pass


def _validate_required(data: Dict[str, Any], keys: list[str], ctx: str) -> None:
    for k in keys:
        if k not in data:
            raise QTreeValidationError(f"Missing required key '{k}' in {ctx}")


def load_qtree_from_yaml(path: str) -> QTreeDefinition:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Q&A YAML not found: {path}")

    raw = yaml.safe_load(yaml_path.read_text())
    _validate_required(raw, ["version", "namespace", "user_type", "tree_id", "root_question_id", "questions"], "qtree")

    questions: Dict[str, QuestionNode] = {}
    for q_id, q_data in raw["questions"].items():
        _validate_required(q_data, ["text", "type"], f"question {q_id}")
        follow_ups = {}
        if "follow_ups" in q_data:
            fu = q_data["follow_ups"]
            if isinstance(fu, dict):
                # Accept nested "on_value" key or direct mapping
                if "on_value" in fu and isinstance(fu["on_value"], dict):
                    follow_ups = fu["on_value"]
                else:
                    follow_ups = fu

        question = QuestionNode(
            id=q_id,
            user_type=raw["user_type"],
            text=q_data["text"],
            attribute=q_data.get("attribute"),
            qtype=q_data.get("type", "free_text"),
            classifier=q_data.get("classifier"),
            options=q_data.get("options", []) or [],
            follow_ups=follow_ups,
            end_of_tree=bool(q_data.get("end_of_tree", False)),
        )
        questions[q_id] = question

    if raw["root_question_id"] not in questions:
        raise QTreeValidationError("root_question_id must exist in questions")

    return QTreeDefinition(
        version=int(raw["version"]),
        namespace=str(raw["namespace"]),
        user_type=str(raw["user_type"]),
        tree_id=str(raw["tree_id"]),
        root_question_id=str(raw["root_question_id"]),
        questions=questions,
    )
