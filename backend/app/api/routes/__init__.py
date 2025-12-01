from fastapi import APIRouter

from . import (
    agent,
    agent_candidates,
    agent_jobs,
    applications,
    chat_routes,
    auth,
    candidates,
    jobs,
    matching,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agent.router)
api_router.include_router(candidates.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(matching.router)
api_router.include_router(agent_jobs.router)
api_router.include_router(agent_candidates.router)
api_router.include_router(chat_routes.router)
