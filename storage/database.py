"""SQLite dedup — never feature the same repo twice."""
from __future__ import annotations
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pulse.db")


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS seen_repos (
            full_name TEXT PRIMARY KEY,
            first_seen TEXT,
            featured_on TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_number INTEGER,
            repos TEXT,
            success INTEGER,
            sent_at TEXT,
            error TEXT
        )""")


def filter_new(repos: list[dict]) -> list[dict]:
    """Return only repos not yet featured."""
    with _conn() as c:
        new = []
        for repo in repos:
            fn = repo.get("full_name", "")
            row = c.execute("SELECT 1 FROM seen_repos WHERE full_name=?", (fn,)).fetchone()
            if not row:
                new.append(repo)
        return new


def save_repos(repos: list[dict]):
    from datetime import date
    today = date.today().isoformat()
    with _conn() as c:
        for repo in repos:
            fn = repo.get("full_name", "")
            c.execute(
                "INSERT OR IGNORE INTO seen_repos (full_name, first_seen) VALUES (?,?)",
                (fn, today)
            )


def mark_featured(repos: list[dict]):
    from datetime import date
    today = date.today().isoformat()
    with _conn() as c:
        for repo in repos:
            fn = repo.get("full_name", "")
            c.execute("UPDATE seen_repos SET featured_on=? WHERE full_name=?", (today, fn))


def get_issue_number() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) FROM email_log WHERE success=1").fetchone()
        return (row[0] or 0) + 1


def log_email(issue: int, repos: list[str], success: bool, error: str = ""):
    from datetime import datetime
    with _conn() as c:
        c.execute(
            "INSERT INTO email_log (issue_number,repos,success,sent_at,error) VALUES (?,?,?,?,?)",
            (issue, ",".join(repos), int(success), datetime.utcnow().isoformat(), error)
        )


def get_total_seen() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) FROM seen_repos").fetchone()
        return row[0] or 0


def _conn():
    return sqlite3.connect(DB_PATH)
