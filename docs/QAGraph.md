# Q&A Graph Architecture

This doc describes the Q&A graph model, how YAML trees are loaded, and how the LangGraph router interacts with agents.

## Graph model (openCypher)
- Nodes: `User`, `Job`, `Question`, `Answer`, `Concept`, `QTree`, (future) `RoleProfile`.
- Edges:
  - `(:User)-[:GAVE_ANSWER]->(:Answer)-[:ABOUT]->(:Question)`
  - `(:User)-[:HAS_TRAIT {attribute, normalized_value, strength, confidence}]->(:Concept)`
  - `(:Job)-[:REQUIRES_SKILL {attribute, weight, required}]->(:Concept)`
  - `(:Question)-[:NEXT {value}]->(:Question)`
  - `(:QTree)-[:HAS_QUESTION]->(:Question)`
  - (optional) `(:Job)-[:INSTANCE_OF]->(:RoleProfile)`
  - (optional) `(:RoleProfile)-[:PREFERS_ANSWER {question_id, value, weight}]->(:Concept)`

## YAML-defined Q&A trees
- Located at `backend/app/qna_graph/config/*.yaml`.
- Loaded at startup and upserted into the graph.
- Each tree has `user_type`, `tree_id`, `root_question_id`, and per-question config (text, type, attribute, classifier, follow-ups).
- Follow-ups map `normalized_value -> next_question_id` (with optional `default`).

## Router & agents
- **Router agent** (`backend/app/agents/router_agent.py`):
  - Entry point for chat.
  - Routes to:
    - Q&A agent (onboarding or if already mid-flow).
    - General chat agent (existing recruiter assistant).
    - Calendar stub (keyword-based scheduling intent).
- **Q&A agent** (`backend/app/agents/qna_agent.py`):
  - `ask_next_question` fetches the next question from the graph/QTree and appends it to messages.
  - `process_answer` classifies answers (Instructor + heuristics), records `Answer` + `HAS_TRAIT` edges, and advances the tree.
- **General chat agent** (`backend/app/agents/general_chat_agent.py`):
  - Calls existing `run_agent_chat` for default behavior.
- **Calendar stub** (`backend/app/agents/calendar_agent_stub.py`):
  - Acknowledges scheduling intent; TODO: integrate real calendar.

## Scoring helpers
- `backend/app/qna_graph/scoring.py`:
  - `compute_job_user_score` runs Cypher:
    ```
    MATCH (j:Job {id:$job_id})-[req:REQUIRES_SKILL]->(c:Concept)<-[has:HAS_TRAIT]-(u:User {id:$user_id})
    WITH req.attribute AS attr, req, has
    WITH attr, sum(req.weight * has.strength * has.confidence) AS attr_score
    RETURN sum(attr_score) AS total_match_score, collect({attribute: attr, score: attr_score}) AS breakdown
    ```
  - `explain_attribute` fetches trait/answer context for an attribute.

## Running the router
- Backend startup loads YAML, initializes the graph client, and compiles the LangGraph router.
- Chat endpoint: `POST /api/v1/chat/router` with `{ message, messages?[], user_type?, qna_tree_id? }`.
- Response includes updated `messages`, `qna_mode`, `current_question_id`, and `qna_tree_id`.

## Extending
- Add YAML in `backend/app/qna_graph/config/` and restart/redeploy.
- Implement new classifier dataclasses and plug them into `qna_agent.classify_with_instructor`.
- Add new specialized agents, then extend `router_agent` routing logic and edges.
