import numpy as np
import pandas as pd
import config

def _first_last_valid(series: pd.Series) -> tuple[pd.Timestamp, pd.Timestamp, float, float] | None:
    clean = series.dropna()
    if len(clean) < 2:
        return None
    return clean.index[0], clean.index[-1], float(clean.iloc[0]), float(clean.iloc[-1])

def simple_return(series: pd.Series) -> float | None:
    fl = _first_last_valid(series)
    if fl is None: 
        return None
    _, _, start, end = fl
    return (end - start)/ start * 100

def annualized_return(series: pd.Series) -> float | None:
    fl = _first_last_valid(series)
    if fl is None:
        return None
    start_date, end_date, start, end = fl
    years = (end_date - start_date).days / 365.25
    if years <= 0 or start <= 0:
        return None
    return ((end/start) ** (1/years) - 1) * 100

def common_window_return( prices: pd.DataFrame, tickers: list[str]) -> tuple[dict[str, float], pd.Timestamp | None, pd.Timestamp | None]:
    cols = [t for t in tickers if t in prices.columns and prices[t].notna().any()]
    if len(cols) < 2:
        return {}, None, None
    
    sub = prices[cols].dropna()
    if sub.empty:
        return {}, None, None
    
    start, end = sub.index[0], sub.index[-1]
    returns = {t: (sub[t].iloc[-1] - sub[t].iloc[0])/sub[t].iloc[0] * 100 for t in cols}

    return returns, start, end

def daily_returns(series: pd.Series) -> pd.Series:
    return series.dropna().pct_change().dropna()

def normalize_to_base(prices: pd.DataFrame, base: float = 100) -> pd.DataFrame:
    out = {}
    for c in prices.columns:
        clean = prices[c].dropna()
        if clean.empty:
            continue
        out[c] = prices[c] / clean.iloc[0] * base

    return pd.DataFrame(out)

def total_growth(series: pd.Series) -> float | None:
    s = series.dropna().sort_index()
    if len(s) < 2 or s.iloc[0] == 0:
            return None
    return (s.iloc[-1] - s.iloc[0]) / abs(s.iloc[0]) * 100