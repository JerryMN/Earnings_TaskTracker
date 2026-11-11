"""SQLite schema and connection lifecycle; no third-party dependencies required."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3


DEFAULT_SETTINGS = {
    "personal_target_hours": 35.0,
    "tier_threshold_minutes": 30.0,
    "bonus_milestones": [
        {"hours": 20.0, "bonus": 43.50},
        {"hours": 35.0, "bonus": 101.50},
    ],
    "extra_earnings": 0.0,
    "use_live_fx": False,
    "usd_mxn_rate": 18.50,
    "usd_mxn_source": "manual",
    "usd_mxn_last_updated": "",
}


def database_path():
    """Use a project-relative default, independent of the launch directory."""
    override = os.environ.get("EARNINGS_DB_PATH")
    return Path(override).expanduser().resolve() if override else Path(__file__).resolve().parent / "data" / "earnings.sqlite3"


@contextmanager
def connect(db_path=None):
    """Commit successful writes, roll back failures, and always close the connection."""
    path = Path(db_path) if db_path is not None else database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(db_path=None):
    """Create missing tables and defaults without overwriting existing data."""
    with connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                task TEXT NOT NULL,
                minutes INTEGER NOT NULL CHECK (minutes >= 0),
                seconds INTEGER NOT NULL CHECK (seconds BETWEEN 0 AND 59),
                rate_type TEXT NOT NULL CHECK (rate_type IN ('full', 'discounted'))
            )
        """)
        # Rates can be removed independently of historical task records.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS task_rates (
                task TEXT PRIMARY KEY,
                hourly_rate REAL NOT NULL,
                discounted_rate REAL NOT NULL,
                pricing_mode TEXT NOT NULL,
                tier_threshold_minutes REAL NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        connection.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            [(key, json.dumps(value)) for key, value in DEFAULT_SETTINGS.items()],
        )


if __name__ == "__main__":
    initialize_database()
    print(f"Database ready: {database_path()}")
