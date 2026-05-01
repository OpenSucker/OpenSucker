from fastapi import APIRouter, HTTPException

from app.domains.terminals.schemas import TerminalComparison, TerminalInfo
from app.domains.terminals.service import get_all_terminals, get_terminal

router = APIRouter()


@router.get("/", response_model=TerminalComparison, summary="交易终端对比")
def list_terminals() -> TerminalComparison:
    return get_all_terminals()


@router.get("/{terminal_type}", response_model=TerminalInfo, summary="查询单个终端信息")
def get_terminal_info(terminal_type: str) -> TerminalInfo:
    info = get_terminal(terminal_type)
    if info is None:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return info
