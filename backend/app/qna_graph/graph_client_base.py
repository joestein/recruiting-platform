from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional


class GraphClient(abc.ABC):
    """Abstract graph client interface for AGE and Neptune."""

    @abc.abstractmethod
    async def run_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return rows as dicts."""

    @abc.abstractmethod
    async def init_schema(self) -> None:
        """Initialize any required extensions/graph for the backend."""

    @abc.abstractmethod
    async def ensure_graph(self, graph_name: str) -> None:
        """Ensure the graph exists (no-op if already present)."""

    async def close(self) -> None:
        """Override if the client needs teardown."""
        return None
