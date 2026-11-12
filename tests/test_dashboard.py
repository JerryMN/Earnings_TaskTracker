from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from database import initialize_database
from storage import add_task, load_settings, load_tasks, save_settings, save_task_rates


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.sqlite3"
        env = patch.dict("os.environ", {"EARNINGS_DB_PATH": str(self.path)})
        env.start()
        self.addCleanup(env.stop)
        initialize_database()
        save_settings({"usd_mxn_rate": 20.0, "bonus_milestones": [{"hours": 2.0, "bonus": 10.0}]})
        save_task_rates({
            "Manual": {"hourly_rate": 60.0, "discounted_rate": 30.0},
            "Tiered": {"hourly_rate": 60.0, "discounted_rate": 30.0,
                       "pricing_mode": "tiered", "tier_threshold_minutes": 30.0},
        })
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "dashboard.py"))

    def widget(self, kind, label):
        return next(widget for widget in getattr(self.app, kind) if widget.label == label)

    def run_app(self):
        self.app.run()
        self.assertFalse(self.app.exception)

    def seed(self, day):
        add_task({"date": day, "task": "Manual", "minutes": 60, "seconds": 0, "rate_type": "full"})

    def test_rate_type_updates_and_resets_after_tiered_submission(self):
        self.run_app()
        self.assertEqual(self.widget("selectbox", "Rate type").value, "full")
        self.widget("selectbox", "Task name").select("Tiered")
        self.run_app()
        self.assertNotIn("Rate type", [w.label for w in self.app.selectbox])
        self.widget("number_input", "Minutes").set_value(45)
        next(b for b in self.app.button if "Add task" in b.label).click()
        self.run_app()
        self.assertEqual(self.widget("selectbox", "Task name").value, "Manual")
        self.assertEqual(self.widget("selectbox", "Rate type").value, "full")
        self.assertEqual(load_tasks().iloc[0]["task"], "Tiered")
        self.assertEqual(self.widget("metric", "Earnings (USD)").value, "$37.50")
        self.widget("selectbox", "Task name").select("Tiered")
        self.run_app()
        self.widget("selectbox", "Task name").select("Manual")
        self.run_app()
        self.assertEqual(self.widget("selectbox", "Rate type").value, "full")

    def test_conversion_fee_is_applied_and_persisted(self):
        self.seed("2026-11-01")
        self.run_app()
        self.assertEqual(self.widget("metric", "Earnings (MXN)").value, "$1,146.00")
        for fee, expected in [(0.0, "$1,200.00"), (100.0, "$0.00"), (10.0, "$1,080.00")]:
            self.widget("number_input", "Conversion fee (%)").set_value(fee)
            self.run_app()
            self.assertEqual(self.widget("metric", "Earnings (MXN)").value, expected)
        next(b for b in self.app.button if "Save settings" in b.label).click()
        self.run_app()
        initialize_database()
        self.assertEqual(load_settings()["conversion_fee_percent"], 10.0)

    def test_date_filter_inclusive_empty_and_invalid_ranges(self):
        self.seed("2026-11-01")
        self.seed("2026-11-02")
        self.run_app()
        self.assertEqual(self.widget("metric", "Bonuses earned").value, "$10.00")
        self.widget("checkbox", "Filter by date").check()
        self.run_app()
        self.widget("date_input", "Start date").set_value(date(2026, 11, 2))
        self.run_app()
        self.assertEqual(self.widget("metric", "Number of tasks").value, "1")
        self.assertEqual(self.widget("metric", "Total hours").value, "1.00 h")
        self.assertEqual(self.widget("metric", "Bonuses earned").value, "$0.00")
        self.assertEqual(self.widget("metric", "Earnings (USD)").value, "$60.00")
        self.assertEqual(len(self.app.dataframe[-1].value), 1)
        self.widget("date_input", "Start date").set_value(date(2026, 11, 3))
        self.widget("date_input", "End date").set_value(date(2026, 11, 3))
        self.run_app()
        self.assertEqual(self.widget("metric", "Number of tasks").value, "0")
        self.widget("date_input", "End date").set_value(date(2026, 11, 1))
        self.run_app()
        self.assertTrue(self.app.error)
        self.widget("checkbox", "Filter by date").uncheck()
        self.run_app()
        self.assertEqual(self.widget("metric", "Number of tasks").value, "2")
