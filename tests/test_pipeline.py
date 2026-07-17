import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline
import analytics


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pipeline.generate_data(order_count=250)
        pipeline.validate(cls.data)
        pipeline.build_database(cls.data)

    def test_expected_row_counts(self):
        self.assertEqual(len(self.data["orders"]), 250)
        self.assertEqual(len(self.data["shipments"]), 250)
        self.assertGreater(len(self.data["order_lines"]), 250)

    def test_referential_integrity(self):
        with sqlite3.connect(pipeline.DB_PATH) as connection:
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(violations, [])

    def test_inventory_snapshot_is_complete(self):
        expected = len(self.data["warehouses"]) * len(self.data["products"])
        with sqlite3.connect(pipeline.DB_PATH) as connection:
            actual = connection.execute("SELECT COUNT(*) FROM inventory_snapshots").fetchone()[0]
            negative_available = connection.execute("""
                SELECT COUNT(*) FROM inventory_snapshots
                WHERE on_hand_units < allocated_units
            """).fetchone()[0]
        self.assertEqual(actual, expected)
        self.assertEqual(negative_available, 0)

    def test_kpis_are_plausible(self):
        with sqlite3.connect(pipeline.DB_PATH) as connection:
            delivered, on_time = connection.execute("""
                SELECT COUNT(*), SUM(sh.delivery_date <= o.promised_date)
                FROM orders o JOIN shipments sh USING(order_id)
                WHERE o.order_status='Delivered'
            """).fetchone()
        self.assertGreater(delivered, 0)
        self.assertGreater(on_time / delivered, 0.25)
        self.assertLessEqual(on_time / delivered, 1.0)

    def test_exception_queue_is_ranked(self):
        with sqlite3.connect(pipeline.DB_PATH) as connection:
            exceptions = analytics.priority_exceptions(connection, 10)
        self.assertGreater(len(exceptions), 0)
        exposures = [row[6] for row in exceptions]
        self.assertEqual(exposures, sorted(exposures, reverse=True))
        self.assertTrue(all(row[7].startswith(("P1", "P2")) for row in exceptions))

    def test_intervention_scenario_improves_service(self):
        with sqlite3.connect(pipeline.DB_PATH) as connection:
            scenario = analytics.intervention_scenario(connection)
        self.assertGreater(scenario["additional_on_time_orders"], 0)
        self.assertGreater(scenario["scenario_on_time_pct"], scenario["baseline_on_time_pct"])
        self.assertLessEqual(scenario["scenario_on_time_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
