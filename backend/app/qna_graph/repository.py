from __future__ import annotations

from typing import Any, Dict, List, Optional

from .graph_client_base import GraphClient
from .models import AnswerRecord, HasTraitEdge, QTreeDefinition, QuestionNode


class QnaGraphRepository:
    """Repository for Q&A graph persistence and queries."""

    def __init__(self, graph_client: GraphClient, graph_name: str) -> None:
        self.client = graph_client
        self.graph_name = graph_name

    async def init_graph_schema(self) -> None:
        await self.client.ensure_graph(self.graph_name)
        await self.client.init_schema()
        # Minimal indexes could be added here for AGE. Using MERGE-based patterns keeps things idempotent.

    async def upsert_qtree(self, tree: QTreeDefinition) -> None:
        await self.init_graph_schema()

        for q in tree.questions.values():
            cypher = """
            MERGE (t:QTree {tree_id: $tree_id, user_type: $user_type})
            SET t.namespace=$namespace, t.version=$version
            MERGE (q:Question {id: $id, tree_id: $tree_id})
            SET q.user_type=$user_type, q.text=$text, q.attribute=$attribute,
                q.qtype=$qtype, q.namespace=$namespace, q.end_of_tree=$end_of_tree,
                q.generation_prompt=$generation_prompt
            MERGE (t)-[:HAS_QUESTION]->(q)
            """
            params = {
                "tree_id": tree.tree_id,
                "user_type": tree.user_type,
                "namespace": tree.namespace,
                "version": tree.version,
                "id": q.id,
                "text": q.text,
                "attribute": q.attribute,
                "qtype": q.qtype,
                "end_of_tree": q.end_of_tree,
                "generation_prompt": q.generation_prompt,
            }
            await self.client.run_cypher(cypher, params)

            # Follow-ups
            for value, next_id in (q.follow_ups or {}).items():
                cypher_fu = """
                MATCH (q1:Question {id:$qid, tree_id:$tree_id})
                MATCH (q2:Question {id:$next_id, tree_id:$tree_id})
                MERGE (q1)-[r:NEXT {value:$value}]->(q2)
                """
                await self.client.run_cypher(
                    cypher_fu,
                    {"qid": q.id, "tree_id": tree.tree_id, "next_id": next_id, "value": value},
                )

    async def record_answer(self, answer: AnswerRecord, traits: List[HasTraitEdge]) -> None:
        await self.init_graph_schema()
        cypher = """
        MERGE (u:User {id:$user_id})
        MERGE (q:Question {id:$question_id})
        CREATE (a:Answer {
            question_id:$question_id,
            raw_text:$raw_text,
            normalized_value:$normalized_value,
            confidence:$confidence,
            timestamp:$timestamp,
            source:$source
        })
        MERGE (u)-[:GAVE_ANSWER]->(a)
        MERGE (a)-[:ABOUT]->(q)
        """
        await self.client.run_cypher(
            cypher,
            {
                "user_id": answer.user_id,
                "question_id": answer.question_id,
                "raw_text": answer.raw_text,
                "normalized_value": answer.normalized_value,
                "confidence": answer.confidence,
                "timestamp": answer.timestamp.isoformat(),
                "source": answer.source,
            },
        )

        for trait in traits:
            cypher_trait = """
            MERGE (u:User {id:$user_id})
            MERGE (c:Concept {type:$concept_type, key:$concept_key})
            MERGE (u)-[h:HAS_TRAIT {attribute:$attribute, normalized_value:$normalized_value}]->(c)
            SET h.strength=$strength, h.confidence=$confidence
            """
            await self.client.run_cypher(
                cypher_trait,
                {
                    "user_id": trait.user_id,
                    "concept_type": trait.concept_type,
                    "concept_key": trait.concept_key,
                    "attribute": trait.attribute,
                    "normalized_value": trait.normalized_value,
                    "strength": trait.strength,
                    "confidence": trait.confidence,
                },
            )

    async def get_last_answer(self, user_id: str, tree_id: str) -> Optional[Dict[str, Any]]:
        cypher = """
        MATCH (u:User {id:$user_id})-[:GAVE_ANSWER]->(a:Answer)-[:ABOUT]->(q:Question {tree_id:$tree_id})
        RETURN a.question_id AS question_id, a.normalized_value AS normalized_value, a.timestamp AS ts
        ORDER BY ts DESC
        LIMIT 1
        """
        rows = await self.client.run_cypher(cypher, {"user_id": user_id, "tree_id": tree_id})
        return rows[0] if rows else None

    async def get_answered_question_ids(self, user_id: str, tree_id: str) -> List[str]:
        cypher = """
        MATCH (u:User {id:$user_id})-[:GAVE_ANSWER]->(a:Answer)-[:ABOUT]->(q:Question {tree_id:$tree_id})
        RETURN DISTINCT q.id AS id
        """
        rows = await self.client.run_cypher(cypher, {"user_id": user_id, "tree_id": tree_id})
        return [r.get("id") for r in rows if r.get("id") is not None]

    async def get_user_traits(self, user_id: str) -> Dict[str, Any]:
        cypher = """
        MATCH (u:User {id:$user_id})-[h:HAS_TRAIT]->(c:Concept)
        RETURN h.attribute AS attribute, h.normalized_value AS normalized_value, h.strength AS strength, h.confidence AS confidence, c.key AS concept_key, c.type AS concept_type
        """
        rows = await self.client.run_cypher(cypher, {"user_id": user_id})
        traits: Dict[str, Any] = {}
        for row in rows:
            attr = row.get("attribute")
            if not attr:
                continue
            traits.setdefault(attr, []).append(row)
        return traits

    async def get_question(self, qid: str, tree: QTreeDefinition) -> Optional[QuestionNode]:
        return tree.questions.get(qid)
