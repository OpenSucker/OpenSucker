from app.domains.counters.schemas import CounterComparison, CounterInfo


COUNTER_REGISTRY = {
    "normal": CounterInfo(
        counter_type="normal",
        name="普通柜台",
        latency_ms=80.0,
        throughput=1000,
        supports_quant=False,
        supports_basket=False,
        supports_algorithmic=False,
        cost_level="free",
    ),
    "ldp": CounterInfo(
        counter_type="ldp",
        name="LDP极速柜台",
        latency_ms=15.0,
        throughput=50000,
        supports_quant=True,
        supports_basket=True,
        supports_algorithmic=True,
        cost_level="high",
    ),
    "uft": CounterInfo(
        counter_type="uft",
        name="UFT极速柜台",
        latency_ms=5.0,
        throughput=100000,
        supports_quant=True,
        supports_basket=True,
        supports_algorithmic=True,
        cost_level="high",
    ),
}


def get_all_counters() -> CounterComparison:
    counters = list(COUNTER_REGISTRY.values())
    recommendation = (
        "普通投资者使用 normal；量化/机构低频策略使用 ldp；"
        "高频/套利/极致延迟场景使用 uft。"
    )
    return CounterComparison(counters=counters, recommendation=recommendation)


def get_counter(counter_type: str) -> CounterInfo | None:
    return COUNTER_REGISTRY.get(counter_type)
