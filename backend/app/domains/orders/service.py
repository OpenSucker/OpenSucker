from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domains.orders.schemas import OrderCreate, OrderResponse, OrderLatencyReport


def create_order(data: OrderCreate) -> OrderResponse:
    now = datetime.now(timezone.utc).isoformat()
    latency = _calculate_latency(data.terminal_type, data.counter_type)
    return OrderResponse(
        order_id=str(uuid.uuid4()),
        symbol=data.symbol,
        side=data.side,
        order_type=data.order_type,
        quantity=data.quantity,
        price=data.price,
        status="submitted",
        terminal_type=data.terminal_type,
        counter_type=data.counter_type,
        latency_ms=latency,
        created_at=now,
    )


def _calculate_latency(terminal_type: str, counter_type: str) -> float:
    base_latency = {"mobile": 80.0, "pc": 35.0, "vip": 5.0}
    counter_multiplier = {"normal": 2.0, "ldp": 0.3, "uft": 0.1}
    return base_latency.get(terminal_type, 50.0) * counter_multiplier.get(counter_type, 1.0)


def get_latency_report(orders: list[OrderResponse]) -> list[OrderLatencyReport]:
    from collections import defaultdict
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for o in orders:
        groups[(o.terminal_type, o.counter_type)].append(o.latency_ms)
    reports = []
    for (terminal, counter), latencies in groups.items():
        reports.append(
            OrderLatencyReport(
                terminal_type=terminal,
                counter_type=counter,
                avg_latency_ms=sum(latencies) / len(latencies),
                min_latency_ms=min(latencies),
                max_latency_ms=max(latencies),
                order_count=len(latencies),
            )
        )
    return reports
