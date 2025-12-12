

from datetime import date
from pathlib import Path
import sys
from typing import List, Optional
from adapters.orders import Orders
from core_lib.adapters.filters import Filters

def main(argv: List[str]) -> str:
    orders = Orders()
    data_path = Path(__file__).parent / "data" / "orders.json"

    orders_data = orders.get_orders(data_path)

    filters = Filters()
    args = filters.parse_args(argv)
    from_date: Optional[date] = None
    if args.from_date:
        try:
            from_date = date.fromisoformat(args.from_date)
        except ValueError:
            raise ValueError(f"Invalid -from date: {args.from_date} (expected YYYY-MM-DD)")

    orders_stats = orders.process_orders(orders_data, from_date=from_date)
    return orders.format_output(orders_stats)

if __name__ == "__main__":
    print(main(sys.argv))