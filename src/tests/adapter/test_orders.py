import io
from pathlib import Path
import unittest
from datetime import date

from src.core_lib.adapters.orders import Orders


class TestOrders(unittest.TestCase):
    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.orders = Orders()

    def test_revenue_and_suspicious(self):

        data_path = Path(__file__).parent / "orders_test_1.json"
        orders = self.orders.get_orders(data_path)
        stats = self.orders.process_orders(orders)

        self.assertEqual(stats.total_cents, 300)  # excludes negative
        self.assertEqual(stats.revenue_by_marketplace_cents.get("amazon"), 100)  # excludes negative
        reasons = [s.reason for s in stats.suspicious]
        self.assertIn("empty marketplace", reasons)
        self.assertIn("negative amount (-50)", reasons)

    def test_from_date_filter(self):

        data_path = Path(__file__).parent / "orders_test_2.json"
        orders = self.orders.get_orders(data_path)
        stats = self.orders.process_orders(orders, from_date=date.fromisoformat("2024-11-01"))

        self.assertEqual(stats.total_cents, 200)
        self.assertEqual(stats.revenue_by_marketplace_cents.get("amazon"), 200)


if __name__ == "__main__":
    unittest.main()
