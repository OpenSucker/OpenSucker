from fastapi import APIRouter, HTTPException

from app.domains.counters.schemas import CounterComparison, CounterInfo
from app.domains.counters.service import get_all_counters, get_counter

router = APIRouter()


@router.get("/", response_model=CounterComparison, summary="券商柜台对比")
def list_counters() -> CounterComparison:
    return get_all_counters()


@router.get("/{counter_type}", response_model=CounterInfo, summary="查询单个柜台信息")
def get_counter_info(counter_type: str) -> CounterInfo:
    info = get_counter(counter_type)
    if info is None:
        raise HTTPException(status_code=404, detail="Counter not found")
    return info
