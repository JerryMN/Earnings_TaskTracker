"""Dashboard persistence, kept separate from Streamlit for reuse and testing.

Call initialize_database() once at application startup before using these helpers.
"""

import json

from database import DEFAULT_SETTINGS, connect


def load_settings(db_path=None):
    with connect(db_path) as connection:
        return {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT key, value FROM settings")}


def save_settings(settings, db_path=None):
    rows = [(key, json.dumps(value)) for key, value in settings.items()]
    with connect(db_path) as connection:
        connection.executemany("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", rows)


def load_task_rates(db_path=None):
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM task_rates ORDER BY rowid").fetchall()
    return {row["task"]: {key: row[key] for key in row.keys() if key != "task"} for row in rows}


def save_task_rates(rates, db_path=None):
    rows = [(
        name, float(rate.get("hourly_rate", 0.0)),
        float(rate.get("discounted_rate", 0.0)),
        rate.get("pricing_mode", "manual"),
        float(rate.get("tier_threshold_minutes", DEFAULT_SETTINGS["tier_threshold_minutes"])),
    ) for name, rate in rates.items()]
    with connect(db_path) as connection:
        connection.execute("DELETE FROM task_rates")
        connection.executemany("""
            INSERT INTO task_rates
                (task, hourly_rate, discounted_rate, pricing_mode, tier_threshold_minutes)
            VALUES (?, ?, ?, ?, ?)
        """, rows)


def load_tasks(db_path=None):
    import pandas as pd

    with connect(db_path) as connection:
        return pd.read_sql_query(
            "SELECT id, date, task, minutes, seconds, rate_type FROM tasks ORDER BY id",
            connection,
        )


def add_task(task, db_path=None):
    with connect(db_path) as connection:
        cursor = connection.execute("""
            INSERT INTO tasks (date, task, minutes, seconds, rate_type)
            VALUES (?, ?, ?, ?, ?)
        """, (str(task["date"]), task["task"], int(task["minutes"]), int(task["seconds"]), task["rate_type"]))
        return cursor.lastrowid


def delete_tasks(task_ids, db_path=None):
    with connect(db_path) as connection:
        connection.executemany("DELETE FROM tasks WHERE id = ?", [(int(task_id),) for task_id in task_ids])


def clear_tasks(db_path=None):
    with connect(db_path) as connection:
        connection.execute("DELETE FROM tasks")
