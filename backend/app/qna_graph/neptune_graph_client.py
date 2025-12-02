from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import aiohttp

from .graph_client_base import GraphClient


class NeptuneGraphClient(GraphClient):
    """Lightweight openCypher client for Amazon Neptune."""

    def __init__(
        self,
        *,
        endpoint: Optional[str],
        port: Optional[int],
        region: Optional[str],
        use_https: bool = True,
        use_bolt: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.port = port or 8182
        self.region = region
        self.use_https = use_https
        self.use_bolt = use_bolt
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def init_schema(self) -> None:
        # Neptune is schema-less for openCypher; no-op placeholder.
        return None

    async def ensure_graph(self, graph_name: str) -> None:
        # Neptune doesn't require explicit graph creation.
        return None

    async def run_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.endpoint:
            raise RuntimeError("NEPTUNE_ENDPOINT not configured")

        protocol = "https" if self.use_https else "http"
        url = f"{protocol}://{self.endpoint}:{self.port}/openCypher"

        session = await self._get_session()

        payload = {"query": query, "parameters": params or {}}

        async with session.post(url, json=payload) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"Neptune cypher error {resp.status}: {text}")
            data = await resp.json()
            # Neptune returns results under "results"
            return data.get("results", data.get("data", []))

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
