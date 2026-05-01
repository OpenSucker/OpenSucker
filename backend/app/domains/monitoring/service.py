from app.domains.monitoring.schemas import AbnormalSignal, MonitoringReport


def detect_abnormal_signals(symbol: str, price_series: list[dict]) -> MonitoringReport:
    signals = []
    if len(price_series) >= 2:
        latest = price_series[-1]["price"]
        prev = price_series[-2]["price"]
        change = (latest - prev) / prev if prev != 0 else 0
        if abs(change) > 0.05:
            signals.append(
                AbnormalSignal(
                    signal_type="price_spike",
                    severity="high" if abs(change) > 0.07 else "medium",
                    description=f"{symbol} 价格异常波动 {change*100:.2f}%",
                    confidence=min(abs(change) * 10, 1.0),
                )
            )
    return MonitoringReport(
        symbol=symbol,
        signals=signals,
        overall_risk_level="high" if signals else "low",
        summary=f"{symbol} 监测到 {len(signals)} 项异常信号。",
    )
