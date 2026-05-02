"""Tencent (腾讯财经) data loader — China-mainland-friendly free real-data source.

Tencent's `web.ifzq.gtimg.cn` endpoint returns historical OHLCV for US, HK and
A-share equities, and is reachable from China without any API key, token, or
rate-limit. We use it as the **primary** loader for ``us_equity`` and
``hk_equity`` because Yahoo / Stooq are typically blocked from CN networks.

Endpoints (all return JSON):

US equities (returns ALL history; we filter client-side):
    https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?
        param={tencent_symbol},day,{start},{end},320,qfq

HK equities:
    https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?
        param={tencent_symbol},day,{start},{end},320,qfq

A-shares (China):
    https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?
        param={tencent_symbol},day,{start},{end},320,qfq

Tencent symbol mapping:
    TSLA, TSLA.US -> usTSLA.OQ      (NASDAQ — most US tickers)
    BRK-B         -> usBRK-B.A       (NYSE class shares)
    0700.HK       -> hk00700
    600519.SH     -> sh600519
    000001.SZ     -> sz000001

Response payload (US):
    {"code": 0, "data": {"usTSLA.OQ": {"qfqday": [["2024-01-02","248.42",...], ...]}}}

Each kline row is [date, open, close, high, low, volume].
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from backtest.loaders.base import validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_BASE_US = "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get"
_BASE_HK = "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get"
_BASE_CN = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
_HEADERS = {
    "Referer": "https://gu.qq.com/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
_TIMEOUT = 15
_RETRIES = 3
_BACKOFF = 1.6


def _classify(code: str) -> Tuple[str, str, str]:
    """Return (market, base_url, tencent_symbol) for a project symbol.

    market: "us_equity" / "hk_equity" / "a_share" / "unknown"
    """
    c = code.strip().upper()
    if c.endswith(".HK"):
        digits = c[:-3].lstrip("0").zfill(5)
        return "hk_equity", _BASE_HK, f"hk{digits}"
    if c.endswith(".SH"):
        return "a_share", _BASE_CN, f"sh{c[:-3]}"
    if c.endswith(".SZ"):
        return "a_share", _BASE_CN, f"sz{c[:-3]}"
    if c.endswith(".BJ"):
        return "a_share", _BASE_CN, f"bj{c[:-3]}"
    if c.endswith(".US"):
        # Strip .US suffix; default OTC/NASDAQ exchange suffix .OQ.
        return "us_equity", _BASE_US, f"us{c[:-3]}.OQ"
    if c.replace(".", "").replace("-", "").isalpha():
        # Bare ticker → assume US, default to NASDAQ class .OQ.
        return "us_equity", _BASE_US, f"us{c}.OQ"
    return "unknown", _BASE_US, f"us{c}.OQ"


def _request_json(url: str, params: Dict[str, str]) -> Optional[dict]:
    last_exc: Optional[Exception] = None
    for attempt in range(1, _RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data
            logger.info("tencent non-zero code for %s: %s", params, data.get("msg"))
            return data
        except Exception as exc:
            last_exc = exc
            logger.warning("tencent attempt %d/%d failed: %s", attempt, _RETRIES, exc)
            if attempt < _RETRIES:
                time.sleep(_BACKOFF ** attempt)
    if last_exc:
        logger.error("tencent exhausted retries: %s", last_exc)
    return None


def _fetch_one(
    code: str,
    start: str,
    end: str,
    *,
    us_exchange_fallbacks: Tuple[str, ...] = (".OQ", ".N", ".A", ""),
) -> pd.DataFrame:
    """Fetch one symbol; for US tickers, walk a few exchange suffixes (NASDAQ/NYSE/AMEX)."""
    market, base_url, tencent_symbol = _classify(code)

    candidates: List[str]
    if market == "us_equity":
        # Strip any existing exchange suffix and try each fallback.
        bare = tencent_symbol
        for suffix in (".OQ", ".N", ".A", ".K"):
            if bare.endswith(suffix):
                bare = bare[: -len(suffix)]
                break
        candidates = [bare + s for s in us_exchange_fallbacks]
    else:
        candidates = [tencent_symbol]

    for sym in candidates:
        params = {"param": f"{sym},day,{start},{end},320,qfq"}
        payload = _request_json(base_url, params)
        if not payload:
            continue
        block = (payload.get("data") or {}).get(sym) or {}
        # Tencent has been observed to return either qfqday or day depending on availability.
        rows = block.get("qfqday") or block.get("day") or block.get("hfqday") or []
        if not rows:
            continue
        df = _rows_to_frame(rows)
        if df.empty:
            continue
        df = df.loc[start:end]
        if df.empty:
            continue
        return df
    return pd.DataFrame()


def _rows_to_frame(rows: List[list]) -> pd.DataFrame:
    """Tencent kline row format: [date, open, close, high, low, volume, ...]."""
    if not rows:
        return pd.DataFrame()
    records = []
    for r in rows:
        if not r or len(r) < 6:
            continue
        try:
            records.append(
                {
                    "trade_date": pd.Timestamp(r[0]),
                    "open": float(r[1]),
                    "close": float(r[2]),
                    "high": float(r[3]),
                    "low": float(r[4]),
                    "volume": float(r[5]),
                }
            )
        except (ValueError, TypeError):
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(records).set_index("trade_date").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


@register
class DataLoader:
    """Tencent 财经 OHLCV loader — CN-friendly, free, no auth, no rate limit."""

    name = "tencent"
    markets = {"us_equity", "hk_equity", "a_share"}
    requires_auth = False

    def is_available(self) -> bool:
        return True

    def __init__(self) -> None:
        pass

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        interval: str = "1D",
    ) -> Dict[str, pd.DataFrame]:
        del fields
        if not codes:
            return {}
        validate_date_range(start_date, end_date)
        if str(interval).upper() not in ("1D", "D", "DAILY"):
            logger.info("tencent loader only supports daily bars; got interval=%s", interval)
            return {}

        out: Dict[str, pd.DataFrame] = {}
        for code in codes:
            try:
                df = _fetch_one(code, start_date, end_date)
                if not df.empty:
                    out[code] = df
                else:
                    logger.info("tencent: no data for %s (%s..%s)", code, start_date, end_date)
            except Exception as exc:
                logger.warning("tencent fetch failed for %s: %s", code, exc)
        return out
