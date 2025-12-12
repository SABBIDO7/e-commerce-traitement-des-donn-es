from decimal import ROUND_HALF_UP, Decimal
import json
from pathlib import Path


from datetime import datetime, date
from typing import Dict, List, Optional

from core_lib.models.order import Order

from core_lib.models.order import Stats, SuspiciousOrder

class Orders:

    def get_orders(self,data_path:Path) -> list[Order]:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        orders: list[Order] = []

        try:
            with open(data_path, encoding="utf-8") as f:
                for line in f:
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
                                "created_at": datetime.strptime(order["created_at"], fmt).date(),
                            }
                        )
                    )

            return orders
        except FileNotFoundError:
            raise FileNotFoundError(f"The path: {data_path} is incorrect")

    def get_total_revenue(self):
        pass

    def suspicious_issues(self,order: Order) -> List[SuspiciousOrder]:
        issues: List[SuspiciousOrder] = []

        if isinstance(order.amount_cents, int) and order.amount_cents < 0:
            issues.append(SuspiciousOrder(order.id, f"negative amount ({order.amount_cents})"))

        mp = (order.marketplace or "").strip()
        if mp == "":
            issues.append(SuspiciousOrder(order.id, "empty marketplace"))

        return issues

    def should_include_by_from_date(self,order: Order, from_date: Optional[date]) -> bool:
        if from_date is None:
            return True
        if not order.created_at:
            return False
        else:
            return order.created_at>= from_date
    
    def process_orders(self,orders: List[Order], from_date: Optional[date] = None) -> Stats:
        """Business logic (testable): compute revenues + suspicious orders."""
        
        total_cents = 0
        by_marketplace: Dict[str, int] = {}
        suspicious: List[SuspiciousOrder] = []
        processed_orders = 0
        invalid_orders = 0

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
            if amount > 0:
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
    