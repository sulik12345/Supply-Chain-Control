import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline


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


if __name__ == "__main__":
    unittest.main()

