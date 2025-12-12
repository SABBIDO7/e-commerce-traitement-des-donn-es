from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Order:
    id: str
    marketplace: Optional[str]
    country: Optional[str]
    amount_cents: Optional[int]
    created_at: Optional[date]

@dataclass
class SuspiciousOrder:
    order_id: str
    reason: str

@dataclass
class Stats:
    total_cents: int
    revenue_by_marketplace_cents: Dict[str, int]
    suspicious: List[SuspiciousOrder]
    processed_orders: int
    invalid_orders: int