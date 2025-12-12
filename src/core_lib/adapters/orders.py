from decimal import ROUND_HALF_UP, Decimal
import json
from pathlib import Path


from datetime import datetime, date
from typing import Dict, List, Optional

from core_lib.models.order import Order

from core_lib.models.order import Stats, SuspiciousOrder

from core_lib.config import DATE_FORMAT, ENCODING

class Orders:

    def get_orders(self,data_path:Path) -> list[Order]:
        """
        Read a JSONL file of orders and parse each line into an Order instance.

        Each line in the file is expected to be a JSON object representing a single order.
        """

        orders: list[Order] = []
        line_number = 0
        try:
            with open(data_path, encoding=ENCODING) as f:
                for line in f:
                    line_number +=1
                    line = line.strip()
                    if not line:
                        continue  # skip empty lines

                    # one JSON order per line
                    order = json.loads(line)

                    # parse created_at into a date
                    orders.append(
                        Order(
                            **{
                                **order,
                                "created_at": datetime.strptime(order["created_at"], DATE_FORMAT).date(),
                            }
                        )
                    )

            return orders
        except FileNotFoundError:
            raise FileNotFoundError(f"The path: {data_path} is incorrect")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON at line {line_number}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field at line {line_number}: {e}")

    def suspicious_issues(self,order: Order) -> List[SuspiciousOrder]:
        """
        Inspect a single order and return the list of detected suspicious issues.

        A suspicious order is one that:
        - has a negative amount_cents
        - or has an empty or missing marketplace
        """

        issues: List[SuspiciousOrder] = []

        if isinstance(order.amount_cents, int) and order.amount_cents < 0:
            issues.append(SuspiciousOrder(order.id, f"negative amount ({order.amount_cents})"))

        mp = (order.marketplace or "").strip()
        if mp == "":
            issues.append(SuspiciousOrder(order.id, "empty marketplace"))

        return issues

    def should_include_by_from_date(self,order: Order, from_date: Optional[date]) -> bool:
        """
        Decide whether an order should be included based on the optional from_date filter.

        If from_date is None, all orders are included.
        """

        if from_date is None:
            return True
        elif not order.created_at:
            return False
        elif not isinstance(order.created_at, date):
           return False 
        else:
            return order.created_at>= from_date
    
    def process_orders(self,orders: List[Order], from_date: Optional[date] = None) -> Stats:
        """
        Process orders and compute revenue statistics.
        
        Args:
            orders: List of Order objects to process
            from_date: Optional filter to include only orders >= this date
            
        Returns:
            Stats object containing total revenue, per-marketplace revenue,
            and list of suspicious orders
            
        Note:
            - Negative amounts are excluded from revenue calculations
            - Orders with missing/invalid amounts are counted as invalid
        """        

        total_cents = 0
        by_marketplace: Dict[str, int] = {}
        suspicious: List[SuspiciousOrder] = []
        processed_orders = 0
        invalid_orders = 0
        MIN_VALID_AMOUNT = 0

        for order in orders:
            if not self.should_include_by_from_date(order, from_date):
                continue

            processed_orders += 1

            amount = order.amount_cents
            if amount is None or not isinstance(amount, int):
                invalid_orders += 1
                suspicious.append(SuspiciousOrder(order.id, "missing/invalid amount_cents"))
                continue

            suspicious.extend(self.suspicious_issues(order))

            # "Reliable stats": ignore negative amounts for revenue calculations
            if amount > MIN_VALID_AMOUNT:
                total_cents += amount
            else:
                continue

            mp = (order.marketplace or "").strip()
            if mp:
                by_marketplace[mp] = by_marketplace.get(mp, 0) + amount

        return Stats(
                total_cents=total_cents,
                revenue_by_marketplace_cents=by_marketplace,
                suspicious=suspicious,
                processed_orders=processed_orders,
                invalid_orders=invalid_orders,
        )
    
    def _cents_to_eur_str(self, cents: int) -> str:
        """Convert integer cents to 'X.YY' string using Decimal to avoid float issues."""
    
        eur = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{eur:.2f}"

    def format_output(self,stats: Stats) -> str:
        """
        Format the computed statistics into a human-readable multi-line string.
        """

        # Sort by revenue in descending order; if equal, fall back to sorting by marketplace name
        items = sorted(
            stats.revenue_by_marketplace_cents.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )

        out: List[str] = []
        out.append(f"Total revenue: {self._cents_to_eur_str(stats.total_cents)} EUR\n")
        out.append("Revenue by marketplace:")
        for mp, cents in items:
            out.append(f"- {mp}: {self._cents_to_eur_str(cents)} EUR")

        out.append("\nSuspicious orders:")
        if not stats.suspicious:
            out.append("- (none)")
        else:
            for s in stats.suspicious:
                out.append(f"- {s.order_id}: {s.reason}")

        return "\n".join(out)
    