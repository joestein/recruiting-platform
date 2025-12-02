from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import AnswerRecord, HasTraitEdge, QTreeDefinition, QuestionNode
from .repository import QnaGraphRepository
from .yaml_loader import QTreeValidationError, load_qtree_from_yaml


class QnaService:
    """High-level Q&A orchestration on top of the graph repository."""

    def __init__(self, repository: QnaGraphRepository) -> None:
        self.repo = repository
        self._trees: Dict[str, QTreeDefinition] = {}
        self._lock = asyncio.Lock()

    async def load_tree_from_file(self, path: str) -> QTreeDefinition:
        tree = load_qtree_from_yaml(path)
        async with self._lock:
            self._trees[tree.tree_id] = tree
        try:
            await self.repo.upsert_qtree(tree)
        except Exception:
            # If graph persistence fails, keep the in-memory tree so Q&A can still run.
            pass
        return tree

    async def preload_directory(self, config_dir: Path) -> List[QTreeDefinition]:
        loaded: List[QTreeDefinition] = []
        if not config_dir.exists():
            return loaded
        for yaml_file in config_dir.glob("*.yaml"):
            loaded.append(await self.load_tree_from_file(str(yaml_file)))
        return loaded

    def get_tree(self, tree_id: str) -> Optional[QTreeDefinition]:
        return self._trees.get(tree_id)

    async def get_next_question_for_user(self, user_id: str, tree_id: str) -> Optional[QuestionNode]:
        tree = self._trees.get(tree_id)
        if not tree:
            return None

        try:
            last = await self.repo.get_last_answer(user_id, tree_id)
        except Exception:
            # On graph fetch errors, fall back to root question
            return tree.questions.get(tree.root_question_id)
        if not last:
            return tree.questions.get(tree.root_question_id)

        current_qid = last.get("question_id")
        normalized_value = last.get("normalized_value")
        current_q = tree.questions.get(current_qid)
        if not current_q:
            return tree.questions.get(tree.root_question_id)

        if current_q.end_of_tree:
            return None

        follow = current_q.follow_ups or {}
        next_id = follow.get(normalized_value) or follow.get("default")
        if next_id:
            return tree.questions.get(next_id)
        # If no follow-up, we are at the end.
        return None

    async def record_answer(
        self,
        *,
        user_id: str,
        question: QuestionNode,
        raw_text: str,
        normalized_value: Optional[str],
        attributes: Dict[str, Any],
        confidence: float,
        traits: List[HasTraitEdge],
    ) -> None:
        answer = AnswerRecord(
            user_id=user_id,
            question_id=question.id,
            raw_text=raw_text,
            normalized_value=normalized_value,
            attributes=attributes,
            confidence=confidence,
            timestamp=datetime.utcnow(),
        )
        await self.repo.record_answer(answer, traits)

    async def get_user_traits(self, user_id: str) -> Dict[str, Any]:
        return await self.repo.get_user_traits(user_id)
