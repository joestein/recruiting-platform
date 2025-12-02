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

    def _inline_params(self, query: str, params: Dict[str, Any]) -> str:
        """
        Inline simple params into a Cypher string. This is a temporary workaround
        for AGE parameter typing quirks; do not use with untrusted user input.
        """
        import re

        def fmt(v: Any) -> str:
            if isinstance(v, str):
                escaped = v.replace('"', '\\"')
                return f"\"{escaped}\""
            if isinstance(v, bool):
                return "true" if v else "false"
            if v is None:
                return "null"
            return str(v)

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            if key in params:
                return fmt(params[key])
            return match.group(0)

        return re.sub(r"\$(\w+)", repl, query)

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
        """
        Execute Cypher against AGE. To avoid signature/typing issues, parameters are inlined
        into the Cypher string. This is safe for our controlled YAML inputs; avoid using with untrusted user strings.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = ag_catalog, \"$user\", public;")
            cypher_query = self._inline_params(query, params or {})
            # Use literal graph name to avoid parameter parsing issues in AGE
            cypher_sql = f"SELECT * FROM cypher('{self.graph_name}', $$ {cypher_query} $$) AS (row agtype);"
            result = await conn.fetch(cypher_sql)
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
