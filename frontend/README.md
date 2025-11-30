# Frontend (Streamlit)

Local development using `uv` + Streamlit.

## Prerequisites
- Python 3.11+
- `uv` installed (`pip install uv`)
- Backend running locally at http://localhost:8000 (or set `API_URL`)

## Run locally
```bash
cd frontend

uv venv
source .venv/bin/activate
uv pip install -e .

# Point to your backend; defaults to http://localhost:8000/api/v1 if unset
export API_URL=${API_URL:-http://localhost:8000/api/v1}

streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

Open: http://localhost:8501

## Notes
- You can also start both frontend/backend via Docker Compose from repo root:
  - `docker compose -f infra/docker-compose.yml up --build`
- If using non-local backend, set `API_URL` to its `/api/v1` base.
