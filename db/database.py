import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/jobs.db")
DB_PATH.parent.mkdir(exist_ok=True)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                title    TEXT,
                company  TEXT,
                location TEXT,
                salary   TEXT,
                link     TEXT,
                source   TEXT,
                work_mode TEXT,
                fetched_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT,
                score      INTEGER,
                grade      TEXT,
                role       TEXT,
                suggestions TEXT
            )
        """)
        conn.commit()


def save_jobs(jobs: list[dict]):
    with get_connection() as conn:
        conn.executemany("""
            INSERT OR IGNORE INTO jobs (title, company, location, salary,
                link, source, work_mode, fetched_at)
            VALUES (:title, :company, :location, :salary, :link, :source,
                :work_mode, :fetched_at)
        """, [
            {**j, "work_mode": j.get("work_mode", ""), "fetched_at": datetime.now().isoformat()}
            for j in jobs
        ])
        conn.commit()


def get_jobs(location="", role="", limit=50):
    with get_connection() as conn:
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        if location:
            query += " AND LOWER(location) LIKE ?"
            params.append(f"%{location.lower()}%")
        if role:
            query += " AND LOWER(title) LIKE ?"
            params.append(f"%{role.lower()}%")
        query += f" ORDER BY fetched_at DESC LIMIT {limit}"
        rows = conn.execute(query, params).fetchall()
        cols = ["id","title","company","location","salary","link",
                "source","work_mode","fetched_at"]
        return [dict(zip(cols, row)) for row in rows]


def save_score_history(record: dict):
    import json
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO score_history (timestamp, score, grade, role, suggestions)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            record["score"], record["grade"],
            record.get("role", "general"),
            json.dumps(record.get("suggestions", []))
        ))
        conn.commit()


def get_score_history(limit=10):
    import json
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM score_history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [{
            "id": r[0], "timestamp": r[1], "score": r[2],
            "grade": r[3], "role": r[4],
            "suggestions": json.loads(r[5] or "[]")
        } for r in rows]