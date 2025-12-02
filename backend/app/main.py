import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import api_router
from .core.config import get_settings
from .qna_graph import get_graph_client
from .qna_graph.repository import QnaGraphRepository
from .qna_graph.service import QnaService
from .agents.router_agent import build_router_graph
from .seed import seed_demo_data

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event() -> None:
    # Initialize graph backend and preload Q&A trees
    graph_client = get_graph_client(settings)
    repo = QnaGraphRepository(graph_client, settings.AGE_GRAPH_NAME)
    qna_service = QnaService(repo)

    config_dir = Path(__file__).parent / "qna_graph" / "config"
    try:
        await qna_service.preload_directory(config_dir)
    except Exception as e:
        logger.error(f"Failed to preload Q&A trees: {e}")
        sys.exit(1)

    app.state.graph_client = graph_client
    app.state.qna_repo = repo
    app.state.qna_service = qna_service
    app.state.router_graph = build_router_graph(qna_service)

    # Seed demo data (org, user, job) if YAML present
    seed_demo_data(settings.SEED_JOBS_FILE, settings.SEED_DEMO_PASSWORD)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if hasattr(app.state, "graph_client"):
        try:
            await app.state.graph_client.close()
        except Exception:
            # Best-effort cleanup
            pass
