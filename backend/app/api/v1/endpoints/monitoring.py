from fastapi import APIRouter

from app.domains.monitoring.schemas import MonitoringReport
from app.domains.monitoring.service import detect_abnormal_signals

router = APIRouter()


@router.post("/abnormal", response_model=MonitoringReport, summary="盘口异常扫描")
def scan_abnormal(data: dict) -> MonitoringReport:
    symbol = data.get("symbol", "")
    price_series = data.get("price_series", [])
    return detect_abnormal_signals(symbol, price_series)
