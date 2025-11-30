# Backend (FastAPI)

Local development using `uv` + `uvicorn`.

## Prerequisites
- Python 3.11+
- `uv` installed (`pip install uv`)

## Run locally
```bash
cd backend
cp ../.env.example .env   # optional: fill secrets/OpenAI keys

uv venv
source .venv/bin/activate
uv pip install -e .

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docs: http://localhost:8000/docs

## Notes
- Set `MATCHING_USE_OPENAI=true` and `OPENAI_API_KEY` in `.env` to enable embeddings/AI extraction.
- Default DB is SQLite (`SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db`); swap for Postgres for staging/prod.
