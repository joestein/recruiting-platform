from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import asyncpg

from .graph_client_base import GraphClient


class AgeGraphClient(GraphClient):
    """Graph client for Apache AGE (Postgres extension)."""

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 5432,
        database: str = "recruiting",
        user: str = "age",
        password: str = "agepassword",
        graph_name: str = "recruiting_graph",
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.graph_name = graph_name
        self._pool: Optional[asyncpg.pool.Pool] = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> asyncpg.pool.Pool:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await asyncpg.create_pool(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                    )
        return self._pool

    async def init_schema(self) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS age;")
            await conn.execute("LOAD 'age';")
            await conn.execute("SET search_path = ag_catalog, \"$user\", public;")
            await conn.execute(
                "SELECT create_graph($1) WHERE NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name=$1);",
                self.graph_name,
            )

    async def ensure_graph(self, graph_name: str) -> None:
        # graph name is fixed at init; this keeps interface parity.
        if graph_name != self.graph_name:
            self.graph_name = graph_name
        await self.init_schema()

    async def run_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            cypher_sql = f"SELECT * FROM cypher($1, $$ {query} $$, $2::json) AS (row agtype);"
            param_payload = json.dumps(params or {})
            result = await conn.fetch(cypher_sql, self.graph_name, param_payload)
            # AGE returns agtype; convert to python dicts/values when possible
            rows = []
            for r in result:
                val = r.get("row")
                if hasattr(val, "to_python"):
                    rows.append(val.to_python())
                elif isinstance(val, str):
                    try:
                        rows.append(json.loads(val))
                    except Exception:
                        rows.append(val)
                else:
                    rows.append(val)
            return rows

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
