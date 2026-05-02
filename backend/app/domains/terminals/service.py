from app.domains.terminals.schemas import TerminalComparison, TerminalInfo


TERMINAL_REGISTRY = {
    "mobile": TerminalInfo(
        terminal_type="mobile",
        name="手机APP",
        avg_latency_ms=120.0,
        max_throughput=10,
        supports_script=False,
        supports_vip_channel=False,
        geo_limitation=False,
        maintenance_cost=0.0,
    ),
    "pc": TerminalInfo(
        terminal_type="pc",
        name="普通PC交易",
        avg_latency_ms=50.0,
        max_throughput=100,
        supports_script=True,
        supports_vip_channel=False,
        geo_limitation=True,
        maintenance_cost=0.0,
    ),
    "vip": TerminalInfo(
        terminal_type="vip",
        name="VIP交易终端",
        avg_latency_ms=3.0,
        max_throughput=10000,
        supports_script=True,
        supports_vip_channel=True,
        geo_limitation=False,
        maintenance_cost=50000.0,
    ),
}


def get_all_terminals() -> TerminalComparison:
    terminals = list(TERMINAL_REGISTRY.values())
    recommendation = (
        "散户日常操作推荐 mobile；脚本化/半自动化推荐 pc；"
        "高频/量化/机构级需求推荐 vip。"
    )
    return TerminalComparison(terminals=terminals, recommendation=recommendation)


def get_terminal(terminal_type: str) -> TerminalInfo | None:
    return TERMINAL_REGISTRY.get(terminal_type)
