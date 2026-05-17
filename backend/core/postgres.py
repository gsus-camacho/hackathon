"""PostgreSQL (read-only) connection pool for Biofood database."""
import os
import time
import asyncpg
from typing import Optional, Tuple

_pool: Optional[asyncpg.Pool] = None
_cache: dict[str, Tuple[float, object]] = {}
_CACHE_TTL = 60  # seconds


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.environ["PG_HOST"],
            port=int(os.environ["PG_PORT"]),
            database=os.environ["PG_DATABASE"],
            user=os.environ["PG_USERNAME"],
            password=os.environ["PG_PASSWORD"],
            min_size=1,
            max_size=8,
            command_timeout=120,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _cache_key(query: str, args: tuple) -> str:
    return f"{query}::{args}"


async def fetch_all(query: str, *args):
    key = _cache_key(query, args)
    now = time.time()
    cached = _cache.get(key)
    if cached and (now - cached[0] < _CACHE_TTL):
        return cached[1]
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        result = [dict(r) for r in rows]
    _cache[key] = (now, result)
    return result


async def fetch_one(query: str, *args):
    key = _cache_key(query, args)
    now = time.time()
    cached = _cache.get(key)
    if cached and (now - cached[0] < _CACHE_TTL):
        return cached[1]
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        result = dict(row) if row else None
    _cache[key] = (now, result)
    return result
