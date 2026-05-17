"""SQLite compatibility layer for Mongo-style backend persistence."""
import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

DB_PATH = Path(os.environ.get("SQLITE_PATH", Path(__file__).parent.parent / "data" / "bioalert.db"))
_conn: Optional[sqlite3.Connection] = None
_lock = asyncio.Lock()


async def init_sqlite() -> None:
    global _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")
    await _create_tables()


async def _run(sql: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
    assert _conn is not None
    async with _lock:
        return await asyncio.to_thread(_conn.execute, sql, params)


async def _fetchall(sql: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
    cursor = await _run(sql, params)
    return await asyncio.to_thread(cursor.fetchall)


async def _fetchone(sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
    cursor = await _run(sql, params)
    return await asyncio.to_thread(cursor.fetchone)


async def _commit() -> None:
    assert _conn is not None
    async with _lock:
        await asyncio.to_thread(_conn.commit)


async def _create_tables() -> None:
    assert _conn is not None
    table_sql = [
        "CREATE TABLE IF NOT EXISTS packages (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS recommendations (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS allergens (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS notifications (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS bot_sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS meal_plans (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS hijos (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS product_votes (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT, updated_at TEXT)",
    ]
    for sql in table_sql:
        await _run(sql)
    await _commit()


def get_db() -> "SQLiteDatabase":
    if _conn is None:
        raise RuntimeError("SQLite database connection not initialized. Call init_sqlite() first.")
    return SQLiteDatabase(_conn)


async def close_sqlite() -> None:
    global _conn
    if _conn is not None:
        await asyncio.to_thread(_conn.close)
        _conn = None


class SQLiteDatabase:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __getattr__(self, name: str) -> "SQLiteCollection":
        return SQLiteCollection(self._conn, name)


class SQLiteCursor:
    def __init__(self, conn: sqlite3.Connection, table: str, where: str, params: List[Any], order: str = ""):
        self._conn = conn
        self._table = table
        self._where = where
        self._params = params
        self._order = order

    def sort(self, sort: Any) -> "SQLiteCursor":
        self._order = _compile_sort(sort)
        return self

    async def to_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        query = f"SELECT data FROM {self._table} WHERE {self._where}"
        if self._order:
            query += f" ORDER BY {self._order}"
        query += f" LIMIT {limit}"
        rows = await _fetchall(query, tuple(self._params))
        return [json.loads(row["data"]) for row in rows]


class SQLiteCollection:
    def __init__(self, conn: sqlite3.Connection, table: str):
        self._conn = conn
        self._table = table

    async def insert_one(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in doc or doc["id"] is None:
            doc["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        doc.setdefault("created_at", now)
        doc.setdefault("updated_at", now)
        data = json.dumps(doc)
        await _run(
            f"INSERT OR REPLACE INTO {self._table} (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (doc["id"], data, doc["created_at"], doc["updated_at"]),
        )
        await _commit()
        return doc

    def find(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> SQLiteCursor:
        where, params = _compile_query(query or {})
        return SQLiteCursor(self._conn, self._table, where, params)

    async def find_one(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        cursor = self.find(query or {}, projection)
        if sort is not None:
            cursor.sort(sort)
        results = await cursor.to_list(1)
        return results[0] if results else None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> SimpleNamespace:
        existing = await self.find_one(query)
        if existing is not None:
            _apply_update(existing, update)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            await _run(
                f"UPDATE {self._table} SET data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(existing), existing["updated_at"], existing["id"]),
            )
            await _commit()
            return SimpleNamespace(modified_count=1)
        if upsert:
            new_doc = {**query}
            if "$set" in update and isinstance(update["$set"], dict):
                new_doc.update(update["$set"])
            inserted = await self.insert_one(new_doc)
            return SimpleNamespace(modified_count=1, upserted_id=inserted["id"])
        return SimpleNamespace(modified_count=0)

    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> SimpleNamespace:
        rows = await self.find(query).to_list(10000)
        modified = 0
        for row in rows:
            _apply_update(row, update)
            row["updated_at"] = datetime.now(timezone.utc).isoformat()
            await _run(
                f"UPDATE {self._table} SET data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(row), row["updated_at"], row["id"]),
            )
            modified += 1
        await _commit()
        return SimpleNamespace(modified_count=modified)

    async def delete_one(self, query: Dict[str, Any]) -> SimpleNamespace:
        row = await self.find_one(query)
        if not row:
            return SimpleNamespace(deleted_count=0)
        await _run(f"DELETE FROM {self._table} WHERE id = ?", (row["id"],))
        await _commit()
        return SimpleNamespace(deleted_count=1)

    async def count_documents(self, query: Dict[str, Any]) -> int:
        where, params = _compile_query(query)
        row = await _fetchone(f"SELECT COUNT(*) as c FROM {self._table} WHERE {where}", tuple(params))
        return int(row["c"]) if row else 0

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        match_stage = pipeline[0].get("$match", {}) if pipeline else {}
        rows = await self.find(match_stage).to_list(10000)
        group_stage = pipeline[1].get("$group", {}) if len(pipeline) > 1 else {}
        results: Dict[Any, Dict[str, Any]] = {}

        for doc in rows:
            group_key = None
            if isinstance(group_stage.get("_id"), str) and group_stage["_id"].startswith("$"):
                group_key = doc.get(group_stage["_id"][1:])
            else:
                group_key = group_stage.get("_id")

            row = results.setdefault(group_key, {"_id": group_key})
            for alias, expr in group_stage.items():
                if alias == "_id":
                    continue
                if isinstance(expr, dict) and "$sum" in expr:
                    cond = expr["$sum"]
                    if isinstance(cond, dict) and "$cond" in cond:
                        condition, true_val, false_val = cond["$cond"]
                        count = true_val if _evaluate_condition(condition, doc) else false_val
                        row[alias] = row.get(alias, 0) + count
                    else:
                        row[alias] = row.get(alias, 0) + int(cond)
                else:
                    row[alias] = row.get(alias, 0)

        sort_stage = pipeline[2].get("$sort", {}) if len(pipeline) > 2 else {}
        entries = list(results.values())
        if sort_stage:
            for key, direction in reversed(list(sort_stage.items())):
                entries.sort(key=lambda item: item.get(key, 0), reverse=(direction == -1))

        for entry in entries:
            yield entry


def _compile_query(query: Dict[str, Any]) -> Tuple[str, List[Any]]:
    if not query:
        return "1=1", []
    filters: List[str] = []
    params: List[Any] = []
    for key, value in query.items():
        if key == "$or" and isinstance(value, list):
            clauses: List[str] = []
            for sub in value:
                sub_where, sub_params = _compile_query(sub)
                clauses.append(f"({sub_where})")
                params.extend(sub_params)
            filters.append("(" + " OR ".join(clauses) + ")")
        elif key == "$and" and isinstance(value, list):
            clauses: List[str] = []
            for sub in value:
                sub_where, sub_params = _compile_query(sub)
                clauses.append(f"({sub_where})")
                params.extend(sub_params)
            filters.append("(" + " AND ".join(clauses) + ")")
        elif isinstance(value, dict):
            for operator, operand in value.items():
                if operator == "$gte":
                    filters.append(f"json_extract(data, '$.{key}') >= ?")
                    params.append(_compile_value(operand))
                elif operator == "$lte":
                    filters.append(f"json_extract(data, '$.{key}') <= ?")
                    params.append(_compile_value(operand))
                elif operator == "$eq":
                    filters.append(f"json_extract(data, '$.{key}') = ?")
                    params.append(_compile_value(operand))
                else:
                    filters.append(f"json_extract(data, '$.{key}') = ?")
                    params.append(_compile_value(value))
        else:
            filters.append(f"json_extract(data, '$.{key}') = ?")
            params.append(_compile_value(value))
    return " AND ".join(filters) if filters else "1=1", params


def _compile_sort(sort: Any) -> str:
    if not sort:
        return ""
    if isinstance(sort, list):
        return ", ".join(_compile_sort(item) for item in sort)
    if isinstance(sort, tuple):
        field, direction = sort
        direction_sql = "DESC" if direction == -1 else "ASC"
        return f"json_extract(data, '$.{field}') {direction_sql}"
    if isinstance(sort, dict):
        parts: List[str] = []
        for field, direction in sort.items():
            dir_sql = "DESC" if direction == -1 else "ASC"
            parts.append(f"json_extract(data, '$.{field}') {dir_sql}")
        return ", ".join(parts)
    return f"json_extract(data, '$.{sort}') ASC"


def _compile_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    return value


def _apply_update(doc: Dict[str, Any], update: Dict[str, Any]) -> None:
    if "$set" in update and isinstance(update["$set"], dict):
        doc.update(update["$set"])
    else:
        raise ValueError("Unsupported update format")


def _evaluate_condition(condition: Dict[str, Any], doc: Dict[str, Any]) -> bool:
    if "$eq" in condition:
        left, right = condition["$eq"]
        left_field = left[1:] if isinstance(left, str) and left.startswith("$") else left
        return doc.get(left_field) == right
    return False
