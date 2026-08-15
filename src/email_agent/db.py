import os
import sqlite3
from datetime import datetime, timezone

from models import EmailRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_emails (
    gmail_id      TEXT PRIMARY KEY,
    sender        TEXT NOT NULL,
    subject       TEXT NOT NULL,
    snippet       TEXT,
    category      TEXT NOT NULL,
    confidence    REAL NOT NULL,
    reasoning     TEXT,
    model_used    TEXT NOT NULL,
    processed_at  TEXT NOT NULL,
    human_override TEXT  -- filled in later if you correct a misclassification
);
"""


class Database:
    def __init__(self, path: str = "data/agent.db"):
        # sqlite3.connect() will NOT create missing parent directories —
        # it only creates the file itself, and only if the directory
        # already exists. This matters once the project is invoked from
        # a different working directory than you developed it in (e.g.
        # `python3 src/email_agent/main.py` from the repo root instead of
        # `python3 main.py` from inside the package folder).
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def already_processed(self, gmail_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM processed_emails WHERE gmail_id = ?", (gmail_id,)
        )
        return cur.fetchone() is not None

    def save(self, record: EmailRecord) -> None:
        self.conn.execute(
            """INSERT OR IGNORE INTO processed_emails
               (gmail_id, sender, subject, snippet, category, confidence,
                reasoning, model_used, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.gmail_id,
                record.sender,
                record.subject,
                record.snippet,
                record.category.value,
                record.confidence,
                record.reasoning,
                record.model_used,
                record.processed_at,
            ),
        )
        self.conn.commit()

    def stats(self) -> dict:
        cur = self.conn.execute(
            "SELECT category, COUNT(*) FROM processed_emails GROUP BY category"
        )
        return dict(cur.fetchall())

    def low_confidence(self, threshold: float = 0.6) -> list[sqlite3.Row]:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(
            "SELECT * FROM processed_emails WHERE confidence < ? ORDER BY processed_at DESC",
            (threshold,),
        )
        return cur.fetchall()

    def close(self) -> None:
        self.conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()