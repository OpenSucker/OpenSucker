"""
database.py — SQLite 持久化层 — Sucker 金融版
表结构更新为支持投资画像与交易记录
"""
import sqlite3
import json
import time
import hashlib
import os
from typing import Optional, Dict, List, Any

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "opensucker.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        fingerprint TEXT UNIQUE NOT NULL,
        created_at  INTEGER NOT NULL,
        updated_at  INTEGER NOT NULL,
        -- 金融画像
        cognitive_level  INTEGER DEFAULT 1,
        risk_preference  TEXT DEFAULT 'moderate',
        investment_style TEXT DEFAULT 'growth',
        capital_size     TEXT DEFAULT 'medium',
        -- 数据资产
        holdings         TEXT DEFAULT '[]',
        watchlist        TEXT DEFAULT '[]',
        historical_lessons TEXT DEFAULT '[]',
        profile_json     TEXT DEFAULT '{}',
        -- 统计
        session_count    INTEGER DEFAULT 0,
        total_messages   INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS conversations (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id),
        session_id  TEXT NOT NULL,
        started_at  INTEGER NOT NULL,
        ended_at    INTEGER,
        message_count INTEGER DEFAULT 0,
        intent_summary TEXT DEFAULT '[]',
        UNIQUE(session_id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        conv_id     TEXT NOT NULL REFERENCES conversations(id),
        user_id     TEXT NOT NULL,
        role        TEXT NOT NULL CHECK(role IN ('user','assistant')),
        content     TEXT NOT NULL,
        intent      TEXT,
        intent_cn   TEXT,
        x_axis      TEXT,
        y_axis      TEXT,
        risk_level  INTEGER DEFAULT 0,
        created_at  INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_users_fp    ON users(fingerprint);
    CREATE INDEX IF NOT EXISTS idx_conv_user   ON conversations(user_id);
    CREATE INDEX IF NOT EXISTS idx_conv_sess   ON conversations(session_id);
    CREATE INDEX IF NOT EXISTS idx_msg_conv    ON messages(conv_id);
    """)
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


def _now() -> int:
    return int(time.time())

def _uid() -> str:
    import uuid
    return str(uuid.uuid4())


# ── 用户 ──────────────────────────────────────────

def get_or_create_user(user_id: str) -> Dict:
    conn = get_conn()
    try:
        # 深度检查：同时匹配 ID 或 Fingerprint，防止旧数据迁移冲突
        row = conn.execute("SELECT * FROM users WHERE id=? OR fingerprint=?", (user_id, user_id)).fetchone()
        if row: return dict(row)

        now = _now()
        # 插入时确保两者一致
        conn.execute("INSERT INTO users(id,fingerprint,created_at,updated_at) VALUES(?,?,?,?)", (user_id, user_id, now, now))
        conn.commit()
        return dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
    finally:
        conn.close()

def update_user_profile(user_id: str, profile: Dict):
    if not profile: return
    allowed = {"cognitive_level", "risk_preference", "investment_style", "capital_size", "holdings", "watchlist", "historical_lessons", "profile_json"}
    fields = {}
    for k, v in profile.items():
        if k not in allowed: continue
        fields[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v

    if not fields: return
    fields["updated_at"] = _now()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [user_id]

    conn = get_conn()
    try:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", values)
        conn.commit()
    finally:
        conn.close()

def get_user_profile(user_id: str) -> Optional[Dict]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row: return None
        d = dict(row)
        for k in ("holdings", "watchlist", "historical_lessons", "profile_json"):
            if d.get(k):
                try: d[k] = json.loads(d[k])
                except: pass
        return d
    finally:
        conn.close()

# ── 会话与消息 (保持不变，已兼容) ──────────────────────────

def get_or_create_conversation(user_id: str, session_id: str) -> str:
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM conversations WHERE session_id=?", (session_id,)).fetchone()
        if row: return row["id"]
        conv_id = _uid()
        conn.execute("INSERT INTO conversations(id,user_id,session_id,started_at) VALUES(?,?,?,?)", (conv_id, user_id, session_id, _now()))
        conn.execute("UPDATE users SET session_count=session_count+1, updated_at=? WHERE id=?", (_now(), user_id))
        conn.commit()
        return conv_id
    finally:
        conn.close()

def save_message(conv_id: str, user_id: str, role: str, content: str, intent: str = None, intent_cn: str = None, x_axis: str = None, y_axis: str = None, risk_level: int = 0):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO messages (conv_id,user_id,role,content,intent,intent_cn,x_axis,y_axis,risk_level,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (conv_id, user_id, role, content, intent, intent_cn, x_axis, y_axis, risk_level, _now()))
        conn.execute("UPDATE conversations SET message_count=message_count+1 WHERE id=?", (conv_id,))
        conn.execute("UPDATE users SET total_messages=total_messages+1, updated_at=? WHERE id=?", (_now(), user_id))
        conn.commit()
    finally:
        conn.close()

def get_conversation_messages(conv_id: str, limit: int = 50) -> List[Dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT role, content, intent_cn, created_at FROM messages WHERE conv_id=? ORDER BY created_at DESC LIMIT ?", (conv_id, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()

def end_conversation(session_id: str):
    conn = get_conn()
    try:
        conn.execute("UPDATE conversations SET ended_at=? WHERE session_id=?", (_now(), session_id))
        conn.commit()
    finally:
        conn.close()

def list_user_conversations(user_id: str, limit: int = 20) -> List[Dict]:
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT c.id, c.session_id, c.started_at, c.ended_at, c.message_count,
                   (SELECT content FROM messages WHERE conv_id=c.id AND role='user' ORDER BY created_at ASC LIMIT 1) as first_message
            FROM conversations c
            WHERE c.user_id=?
            ORDER BY c.started_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            first = d.get("first_message") or ""
            d["title"] = first[:30] + ("..." if len(first) > 30 else "") if first else "新交易会话"
            result.append(d)
        return result
    finally:
        conn.close()

def get_db_stats() -> Dict:
    conn = get_conn()
    try:
        stats = {}
        for table in ("users", "conversations", "messages"):
            row = conn.execute(f"SELECT COUNT(*) as n FROM {table}").fetchone()
            stats[table] = row["n"]
        return stats
    finally:
        conn.close()

if __name__ != "__main__":
    init_db()
