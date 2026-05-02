"""Synthetic data loader — last-resort fallback that generates plausible OHLCV
random walks when no real data source is reachable (network down, rate-limited,
no API token, etc.).

The data is deterministic per (code, start_date, end_date) so repeated runs
produce stable backtest results — useful for demos, tests, and stress-testing
the pipeline itself when external data is unreachable.

⚠️ Data is FAKE. Always emits ``[SYNTHETIC_DATA_FALLBACK]`` to stderr so callers
know the result is simulated, and ``__synthetic__`` is set as a DataFrame attr.
"""

from __future__ import annotations

import hashlib
import sys
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backtest.loaders.base import validate_date_range
from backtest.loaders.registry import register

_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def _seed_for(code: str, start: str, end: str) -> int:
    h = hashlib.sha1(f"{code}|{start}|{end}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def _gbm_series(
    n: int,
    start_price: float,
    mu: float,
    sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Geometric Brownian Motion daily closes."""
    dt = 1.0 / 252.0
    shocks = rng.normal(loc=(mu - 0.5 * sigma ** 2) * dt, scale=sigma * np.sqrt(dt), size=n)
    log_path = np.cumsum(shocks)
    return start_price * np.exp(log_path)


def _build_ohlcv(closes: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    n = len(closes)
    intraday_vol = np.abs(rng.normal(0, 0.012, size=n))
    highs = closes * (1 + intraday_vol)
    lows = closes * (1 - intraday_vol)
    opens = np.empty(n)
    opens[0] = closes[0]
    if n > 1:
        opens[1:] = closes[:-1] * (1 + rng.normal(0, 0.004, size=n - 1))
    opens = np.clip(opens, lows, highs)
    volumes = rng.integers(low=1_000_000, high=20_000_000, size=n).astype(float)
    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        }
    )


@register
class DataLoader:
    """Synthetic OHLCV fallback. Always available, generates fake-but-plausible bars.

    Picks a per-market default drift/vol so a "stress test" looks reasonable
    (e.g. TSLA-style high vol for us_equity, lower vol for forex). Stable across
    runs given the same (code, dates).
    """

    name = "synthetic"
    markets = {"a_share", "us_equity", "hk_equity", "crypto", "futures", "fund", "macro", "forex"}
    requires_auth = False

    _MARKET_PRESETS = {
        "us_equity": {"start_price": 200.0, "mu": 0.10, "sigma": 0.45},
        "a_share":   {"start_price": 30.0,  "mu": 0.05, "sigma": 0.30},
        "hk_equity": {"start_price": 80.0,  "mu": 0.04, "sigma": 0.32},
        "crypto":    {"start_price": 30000.0, "mu": 0.20, "sigma": 0.85},
        "futures":   {"start_price": 4500.0, "mu": 0.03, "sigma": 0.25},
        "fund":      {"start_price": 1.5,   "mu": 0.05, "sigma": 0.18},
        "macro":     {"start_price": 100.0, "mu": 0.02, "sigma": 0.10},
        "forex":     {"start_price": 1.10,  "mu": 0.00, "sigma": 0.08},
    }

    def is_available(self) -> bool:
        return True

    def __init__(self) -> None:
        pass

    def _preset_for(self, code: str) -> Dict[str, float]:
        c = code.upper()
        if c.endswith(".HK"):
            return self._MARKET_PRESETS["hk_equity"]
        if c.endswith(".SZ") or c.endswith(".SH") or c.endswith(".BJ"):
            return self._MARKET_PRESETS["a_share"]
        if "USDT" in c or "USD-" in c or c.endswith("-USD"):
            return self._MARKET_PRESETS["crypto"]
        if "/" in c and len(c) <= 8:
            return self._MARKET_PRESETS["forex"]
        # default: bare ticker → us_equity
        return self._MARKET_PRESETS["us_equity"]

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        interval: str = "1D",
    ) -> Dict[str, pd.DataFrame]:
        del fields, interval
        if not codes:
            return {}
        validate_date_range(start_date, end_date)

        # Business-day calendar (skip weekends; good enough for daily backtests)
        idx = pd.bdate_range(start=start_date, end=end_date)
        if len(idx) == 0:
            return {}

        out: Dict[str, pd.DataFrame] = {}
        for code in codes:
            preset = self._preset_for(code)
            rng = np.random.default_rng(_seed_for(code, start_date, end_date))
            closes = _gbm_series(
                n=len(idx),
                start_price=preset["start_price"],
                mu=preset["mu"],
                sigma=preset["sigma"],
                rng=rng,
            )
            df = _build_ohlcv(closes, rng)
            df.index = idx
            df.index.name = "trade_date"
            df.attrs["__synthetic__"] = True
            out[code] = df
            print(
                f"[SYNTHETIC_DATA_FALLBACK] generated {len(df)} simulated bars for "
                f"{code} ({start_date} → {end_date}); real sources unavailable.",
                file=sys.stderr,
                flush=True,
            )
        return out
