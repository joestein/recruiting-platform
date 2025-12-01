from __future__ import annotations

from typing import Any, Dict, Tuple

from .graph_client_base import GraphClient


async def compute_job_user_score(graph_client: GraphClient, job_id: str, user_id: str) -> Tuple[float, list[dict[str, Any]]]:
    query = """
    MATCH (j:Job {id:$job_id})-[req:REQUIRES_SKILL]->(c:Concept)<-[has:HAS_TRAIT]-(u:User {id:$user_id})
    WITH req.attribute AS attr, req, has
    WITH attr, sum(req.weight * has.strength * has.confidence) AS attr_score
    RETURN sum(attr_score) AS total_match_score, collect({attribute: attr, score: attr_score}) AS breakdown
    """
    rows = await graph_client.run_cypher(query, {"job_id": job_id, "user_id": user_id})
    if not rows:
        return 0.0, []
    row = rows[0]
    total = float(row.get("total_match_score") or 0.0)
    breakdown = row.get("breakdown") or []
    return total, breakdown


async def explain_attribute(graph_client: GraphClient, user_id: str, attribute: str) -> list[dict[str, Any]]:
    query = """
    MATCH (u:User {id:$user_id})-[h:HAS_TRAIT {attribute:$attribute}]->(c:Concept)
    OPTIONAL MATCH (u)-[:GAVE_ANSWER]->(a:Answer {normalized_value:h.normalized_value})-[:ABOUT]->(q:Question)
    RETURN q.id AS question_id, q.text AS question_text, a.raw_text AS raw_answer,
           h.normalized_value AS normalized_value, h.strength AS strength, h.confidence AS confidence
    """
    rows = await graph_client.run_cypher(query, {"user_id": user_id, "attribute": attribute})
    return rows or []
