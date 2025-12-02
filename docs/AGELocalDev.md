# Apache AGE Local Development

## Run AGE with Docker Compose
From repo root:
```bash
docker compose up -d age-db
```

Service details:
- Image: `apache/age:latest`
- Host: `localhost`
- Port: `5432`
- Default creds: `age` / `agepassword`
- DB: `recruiting`

## Backend configuration
Set in `.env` (already in `.env.example`):
```
GRAPH_BACKEND=age
AGE_HOST=localhost
AGE_PORT=5432
AGE_DB=recruiting
AGE_USER=age
AGE_PASSWORD=agepassword
AGE_GRAPH_NAME=recruiting_graph
```

## What startup does
- Loads AGE extension and creates graph `recruiting_graph` if missing.
- Loads YAML Q&A trees from `backend/app/qna_graph/config/*.yaml`.
- Upserts questions/relationships into AGE.

## Validate connectivity
```bash
docker exec -it recruiting-age-db psql -U age -d recruiting -c "SELECT * FROM ag_catalog.ag_graph;"
```

If you see `recruiting_graph`, the extension/graph are ready.

## Using the chat router
- Start backend (with env above) and frontend or Postman.
- Call `POST /api/v1/chat/router` with a message; the router will start the candidate programming-language Q&A flow and store answers in AGE.
