"""会话与附件的 SQLite 持久化（复用项目的 forum.db）。

表结构在 ensure_tables() 里按需创建，随首次导入自动执行，无需改 database/db.py。
"""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from . import config

BACKEND_DIR = config.BACKEND_DIR
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.db import get_db_connection  # noqa: E402


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_tables() -> None:
    db = get_db_connection()
    try:
        cur = db.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_key TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '新对话',
                model TEXT,
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_conv_owner ON agent_conversation(owner_key, update_at)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                meta TEXT,
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_id) REFERENCES agent_conversation(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_msg_conv ON agent_message(conversation_id, id)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_attachment (
                id TEXT PRIMARY KEY,
                owner_key TEXT NOT NULL,
                filename TEXT NOT NULL,
                ext TEXT,
                size INTEGER DEFAULT 0,
                chars INTEGER DEFAULT 0,
                content TEXT NOT NULL,
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_attach_owner ON agent_attachment(owner_key, create_at)"
        )
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------- 会话

def create_conversation(owner_key: str, title: str = "新对话", model: str = "") -> int:
    db = get_db_connection()
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO agent_conversation (owner_key, title, model, create_at, update_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_key, title, model, _now(), _now()),
        )
        db.commit()
        return int(cur.lastrowid)
    finally:
        db.close()


def get_conversation(conv_id: int, owner_key: str) -> dict | None:
    db = get_db_connection()
    try:
        row = db.cursor().execute(
            "SELECT id, title, model, create_at, update_at FROM agent_conversation "
            "WHERE id = ? AND owner_key = ?",
            (conv_id, owner_key),
        ).fetchone()
    finally:
        db.close()
    if not row:
        return None
    return {"id": row[0], "title": row[1], "model": row[2], "create_at": row[3], "update_at": row[4]}


def list_conversations(owner_key: str, limit: int = 50) -> list[dict]:
    db = get_db_connection()
    try:
        rows = db.cursor().execute(
            "SELECT id, title, model, create_at, update_at FROM agent_conversation "
            "WHERE owner_key = ? ORDER BY update_at DESC, id DESC LIMIT ?",
            (owner_key, limit),
        ).fetchall()
    finally:
        db.close()
    return [
        {"id": r[0], "title": r[1], "model": r[2], "create_at": r[3], "update_at": r[4]}
        for r in rows
    ]


def touch_conversation(conv_id: int, title: str | None = None, model: str | None = None) -> None:
    sets = ["update_at = ?"]
    args: list = [_now()]
    if title is not None:
        sets.append("title = ?")
        args.append(title)
    if model is not None:
        sets.append("model = ?")
        args.append(model)
    args.append(conv_id)

    db = get_db_connection()
    try:
        db.execute(f"UPDATE agent_conversation SET {', '.join(sets)} WHERE id = ?", args)
        db.commit()
    finally:
        db.close()


def delete_conversation(conv_id: int, owner_key: str) -> bool:
    db = get_db_connection()
    try:
        cur = db.cursor()
        cur.execute(
            "DELETE FROM agent_conversation WHERE id = ? AND owner_key = ?", (conv_id, owner_key)
        )
        changed = cur.rowcount > 0
        cur.execute("DELETE FROM agent_message WHERE conversation_id = ?", (conv_id,))
        db.commit()
        return changed
    finally:
        db.close()


# ---------------------------------------------------------------- 消息

def add_message(conv_id: int, role: str, content: str, meta: dict | None = None) -> int:
    db = get_db_connection()
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO agent_message (conversation_id, role, content, meta, create_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv_id, role, content, json.dumps(meta or {}, ensure_ascii=False), _now()),
        )
        db.commit()
        return int(cur.lastrowid)
    finally:
        db.close()


def get_messages(conv_id: int, limit: int | None = None) -> list[dict]:
    db = get_db_connection()
    try:
        sql = (
            "SELECT id, role, content, meta, create_at FROM agent_message "
            "WHERE conversation_id = ? ORDER BY id"
        )
        rows = db.cursor().execute(sql, (conv_id,)).fetchall()
    finally:
        db.close()

    msgs = []
    for mid, role, content, meta, created in rows:
        try:
            meta_obj = json.loads(meta) if meta else {}
        except (json.JSONDecodeError, TypeError):
            meta_obj = {}
        msgs.append(
            {"id": mid, "role": role, "content": content, "meta": meta_obj, "create_at": created}
        )
    if limit is not None:
        msgs = msgs[-limit:]
    return msgs


def recent_history(conv_id: int, turns: int = config.MAX_HISTORY_TURNS) -> list[dict]:
    """取最近若干轮用户/助手消息，按字符预算从新到旧裁剪。"""
    msgs = [
        m for m in get_messages(conv_id) if m["role"] in ("user", "assistant") and m["content"]
    ]
    picked: list[dict] = []
    budget = config.MAX_HISTORY_CHARS
    for m in reversed(msgs[-(turns * 2):]):
        cost = len(m["content"])
        if cost > budget and picked:
            break
        budget -= cost
        picked.append(m)
    picked.reverse()
    return picked


# ---------------------------------------------------------------- 附件

def save_attachment(
    owner_key: str, filename: str, ext: str, size: int, content: str
) -> dict[str, Any]:
    att_id = uuid.uuid4().hex
    db = get_db_connection()
    try:
        db.execute(
            "INSERT INTO agent_attachment (id, owner_key, filename, ext, size, chars, content, create_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (att_id, owner_key, filename, ext, size, len(content), content, _now()),
        )
        db.commit()
    finally:
        db.close()
    return {"id": att_id, "filename": filename, "size": size, "chars": len(content)}


def get_attachments(ids: list[str], owner_key: str) -> list[dict]:
    if not ids:
        return []
    db = get_db_connection()
    try:
        placeholders = ",".join("?" for _ in ids)
        rows = db.cursor().execute(
            f"SELECT id, filename, size, chars, content FROM agent_attachment "
            f"WHERE owner_key = ? AND id IN ({placeholders})",
            (owner_key, *ids),
        ).fetchall()
    finally:
        db.close()

    by_id = {
        r[0]: {"id": r[0], "filename": r[1], "size": r[2], "chars": r[3], "content": r[4]}
        for r in rows
    }
    return [by_id[i] for i in ids if i in by_id]


def purge_old_attachments(owner_key: str, keep: int = 20) -> None:
    """附件正文占用较大，只保留每台设备最近 keep 份。"""
    db = get_db_connection()
    try:
        db.execute(
            "DELETE FROM agent_attachment WHERE owner_key = ? AND id NOT IN ("
            "  SELECT id FROM agent_attachment WHERE owner_key = ? "
            "  ORDER BY create_at DESC, rowid DESC LIMIT ?)",
            (owner_key, owner_key, keep),
        )
        db.commit()
    finally:
        db.close()
