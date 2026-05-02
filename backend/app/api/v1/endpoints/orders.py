from fastapi import APIRouter

from app.domains.orders.schemas import OrderCreate, OrderResponse
from app.domains.orders.service import create_order

router = APIRouter()


@router.post("/manual", response_model=OrderResponse, summary="手工自主下单")
def create_manual_order(data: OrderCreate) -> OrderResponse:
    return create_order(data)


@router.post("/quant", response_model=OrderResponse, summary="量化交易下单")
def create_quant_order(data: OrderCreate) -> OrderResponse:
    data.terminal_type = "pc"
    data.counter_type = "uft"
    return create_order(data)
