import argparse
from datetime import date, datetime
from typing import List, Optional
from core_lib.models.order import Order


class Filters:

    def parse_args(self,argv: List[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Compute revenue stats from JSONL orders export.")
        parser.add_argument("path", help="Path to orders.json (JSONL)")
        parser.add_argument(
            "-from",
            dest="from_date",
            default=None,
            help="Optional filter: include only orders with created_at date >= YYYY-MM-DD",
        )
        return parser.parse_args(argv)
