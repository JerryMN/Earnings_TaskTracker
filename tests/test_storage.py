import os
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from database import DEFAULT_SETTINGS, connect, database_path, initialize_database
from storage import (
    add_task, clear_tasks, delete_tasks, load_settings, load_task_rates,
    load_tasks, save_settings, save_task_rates,
)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "nested" / "earnings.sqlite3"
        initialize_database(self.path)

    def task(self, rate_type="full"):
        return {"date": "2026-11-11", "task": "Project's work", "minutes": 32,
                "seconds": 17, "rate_type": rate_type}

    def rows(self):
        with connect(self.path) as connection:
            return connection.execute("SELECT * FROM tasks ORDER BY id").fetchall()

    @unittest.skipUnless(importlib.util.find_spec("pandas"), "pandas is not installed")
    def test_dataframe_shape_and_values(self):
        self.assertEqual(list(load_tasks(self.path).columns),
                         ["id", "date", "task", "minutes", "seconds", "rate_type"])
        self.assertTrue(load_tasks(self.path).empty)
        add_task(self.task("discounted"), self.path)
        row = load_tasks(self.path).iloc[0]
        for key, value in self.task("discounted").items():
            self.assertEqual(row[key], value)

    def test_first_run_and_idempotent_initialization(self):
        self.assertEqual(load_settings(self.path), DEFAULT_SETTINGS)
        self.assertEqual(load_task_rates(self.path), {})
        self.assertEqual(self.rows(), [])
        settings = load_settings(self.path)
        settings["bonus_milestones"] = [{"hours": 4.5, "bonus": 21.75}]
        settings["personal_target_hours"] = 12.5
        save_settings(settings, self.path)
        add_task(self.task(), self.path)
        initialize_database(self.path)
        self.assertEqual(load_settings(self.path), settings)
        self.assertEqual(len(self.rows()), 1)

    def test_missing_defaults_are_restored(self):
        with connect(self.path) as connection:
            connection.execute("DELETE FROM settings WHERE key = 'use_live_fx'")
        initialize_database(self.path)
        self.assertIs(load_settings(self.path)["use_live_fx"], False)

    def test_rates_replace_and_clear_without_deleting_tasks(self):
        rates = {"Project's work": {"hourly_rate": 40.25, "discounted_rate": 12.5,
                 "pricing_mode": "tiered", "tier_threshold_minutes": 30.0}}
        save_task_rates(rates, self.path)
        self.assertEqual(load_task_rates(self.path), rates)
        add_task(self.task(), self.path)
        save_task_rates({"Other": {}}, self.path)
        self.assertEqual(list(load_task_rates(self.path)), ["Other"])
        save_task_rates({}, self.path)
        self.assertEqual(load_task_rates(self.path), {})
        self.assertEqual(len(self.rows()), 1)

    def test_delete_preserves_remaining_rate_types_and_later_inserts(self):
        first = add_task(self.task(), self.path)
        second = add_task(self.task("discounted"), self.path)
        third = add_task(self.task(), self.path)
        delete_tasks([first], self.path)
        rows = self.rows()
        self.assertEqual([row["id"] for row in rows], [second, third])
        self.assertEqual([row["rate_type"] for row in rows], ["discounted", "full"])
        self.assertEqual(rows[0]["task"], "Project's work")
        self.assertEqual(rows[0]["seconds"], 17)
        delete_tasks([], self.path)
        self.assertEqual(len(self.rows()), 2)
        clear_tasks(self.path)
        self.assertEqual(self.rows(), [])
        self.assertEqual(load_settings(self.path), DEFAULT_SETTINGS)

    def test_failed_rate_replacement_rolls_back(self):
        save_task_rates({"Original": {}}, self.path)
        with self.assertRaises(sqlite3.IntegrityError):
            save_task_rates({"Broken": {"pricing_mode": None}}, self.path)
        self.assertEqual(list(load_task_rates(self.path)), ["Original"])

    def test_invalid_task_does_not_change_existing_records(self):
        add_task(self.task(), self.path)
        invalid = dict(self.task(), seconds=60)
        with self.assertRaises(sqlite3.IntegrityError):
            add_task(invalid, self.path)
        self.assertEqual(len(self.rows()), 1)

    def test_default_path_independent_of_working_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            before = database_path()
            old_cwd = Path.cwd()
            try:
                os.chdir(self.temp.name)
                self.assertEqual(database_path(), before)
            finally:
                os.chdir(old_cwd)

    def test_environment_override(self):
        with patch.dict(os.environ, {"EARNINGS_DB_PATH": str(self.path)}):
            self.assertEqual(database_path(), self.path.resolve())
            initialize_database()
            self.assertEqual(load_settings(), DEFAULT_SETTINGS)


if __name__ == "__main__":
    unittest.main()
