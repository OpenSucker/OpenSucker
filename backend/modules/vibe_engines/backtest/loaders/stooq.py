"""Stooq data loader — free, no-auth, no-rate-limit historical OHLCV.

Stooq exposes a public CSV endpoint that returns daily bars for tens of
thousands of global symbols (US/HK/JP/EU equities, indices, FX). It does not
require an API key and has not been observed to throttle. We use it as a
primary fallback for ``us_equity`` (and a secondary for HK) when yfinance is
rate-limited or akshare's network is flaky.

CSV endpoint:
    https://stooq.com/q/d/l/?s={symbol}&i=d&d1={YYYYMMDD}&d2={YYYYMMDD}

Symbol mapping examples:
    TSLA, TSLA.US -> tsla.us
    AAPL          -> aapl.us
    0700.HK       -> 0700.hk
    ^SPX          -> ^spx
"""

from __future__ import annotations

import io
import logging
import time
from typing import Dict, List, Optional

import pandas as pd
import requests

from backtest.loaders.base import validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_STOOQ_URL = "https://stooq.com/q/d/l/"
_TIMEOUT = 15
_RETRIES = 3
_BACKOFF = 1.5


def _to_stooq_symbol(code: str) -> str:
    c = code.strip().upper()
    if c.endswith(".US"):
        return c[:-3].lower() + ".us"
    if c.endswith(".HK"):
        return c[:-3].lower() + ".hk"
    if c.endswith(".SH") or c.endswith(".SZ") or c.endswith(".BJ"):
        # Stooq does not cover Chinese A-shares well; let a different loader handle it.
        return c.lower()
    if c.startswith("^"):
        return c.lower()  # indices
    # Bare alphabetic ticker → assume US
    if c.replace(".", "").isalpha():
        return c.lower() + ".us"
    return c.lower()


def _fetch_one(symbol: str, start: str, end: str) -> pd.DataFrame:
    params = {
        "s": symbol,
        "i": "d",
        "d1": start.replace("-", ""),
        "d2": end.replace("-", ""),
    }
    last_exc: Optional[Exception] = None
    for attempt in range(1, _RETRIES + 1):
        try:
            resp = requests.get(_STOOQ_URL, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            text = resp.text
            if not text or text.lower().startswith("no data") or "exceeded the daily" in text.lower():
                logger.info("stooq: no data for %s (%s..%s)", symbol, start, end)
                return pd.DataFrame()
            df = pd.read_csv(io.StringIO(text))
            if df.empty:
                return df
            return df
        except Exception as exc:
            last_exc = exc
            logger.warning("stooq attempt %d/%d failed for %s: %s", attempt, _RETRIES, symbol, exc)
            if attempt < _RETRIES:
                time.sleep(_BACKOFF ** attempt)
    if last_exc:
        logger.error("stooq exhausted retries for %s: %s", symbol, last_exc)
    return pd.DataFrame()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.rename(columns={c: c.lower() for c in df.columns})
    if "date" not in df.columns:
        return pd.DataFrame()
    df["trade_date"] = pd.to_datetime(df["date"])
    df = df.set_index("trade_date").sort_index()
    cols = ["open", "high", "low", "close", "volume"]
    for col in cols:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[cols].astype(float, errors="ignore")
    return df


@register
class DataLoader:
    """Stooq.com OHLCV loader — free, no auth, no rate limit."""

    name = "stooq"
    markets = {"us_equity", "hk_equity", "macro"}
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
            logger.info("stooq only supports daily bars; skipping for interval=%s", interval)
            return {}

        out: Dict[str, pd.DataFrame] = {}
        for code in codes:
            sym = _to_stooq_symbol(code)
            try:
                raw = _fetch_one(sym, start_date, end_date)
                norm = _normalize(raw)
                if not norm.empty:
                    out[code] = norm
                else:
                    logger.info("stooq returned no usable rows for %s (sym=%s)", code, sym)
            except Exception as exc:
                logger.warning("stooq fetch failed for %s (sym=%s): %s", code, sym, exc)
        return out
