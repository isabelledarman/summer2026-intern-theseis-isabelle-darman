from dataclasses import dataclass
import numpy as np
import pandas as pd
import config
from analysis import returns as R

@dataclass
class RiskMetrics:
    ticker: str
    annual_return: float | None
    annual_vol: float | None
    sharpe: float | None
    sortino: float | None
    max_drawdown: float | None
    beta: float | None
    n_days: int

def _annualized_vol(daily: pd.Series) -> float | None:
    if len(daily) < 2:
        return None
    return float(daily.std() * np.sqrt(config.TRADING_DAYS))

def sharpe_ratio(daily: pd.Series, rf: float | None = None) -> float | None:
    if len(daily) < 2:
        return None
    rf = config.DEFAULT_RISK_FREE if rf is None else rf
    excess_daily = daily.mean() * config.TRADING_DAYS - rf
    vol = _annualized_vol(daily)
    if not vol:
        return None
    return float(excess_daily/vol)

def sortino_ratio(daily: pd.Series, rf: float | None = None) -> float | None:
    if len(daily) < 2:
        return None
    rf = config.DEFAULT_RISK_FREE if rf is None else rf
    downside = daily[daily < 0]
    if len(downside) < 2:
        return None
    downside_vol = float(downside.std() * np.sqrt(config.TRADING_DAYS))
    if not downside_vol: 
        return None
    excess = daily.mean() * config.TRADING_DAYS - rf
    return float(excess/downside_vol)

def max_drawdown(prices: pd.Series) -> float | None:
    clean = prices.dropna()
    if len(clean) < 2:
        return None
    running_max = clean.cummax()
    drawdown = (clean - running_max) /running_max
    return float(drawdown.min() * 100)

def beta(asset_daily: pd.Series, market_daily: pd.Series) -> float | None:
    joined = pd.concat([asset_daily, market_daily], axis = 1, join = "inner").dropna()
    if len(joined) < 2:
        return None
    a, m = joined.iloc[:, 0], joined.iloc[:, 1]
    var_m = m.var()
    if not var_m:
        return None
    return float(a.cov(m) / var_m)

def compute_metrics(prices: pd.DataFrame, ticker: str, market: str = 'SPY', rf: float | None = None
    )-> RiskMetrics:
    series = prices[ticker] if ticker in prices.columns else pd.Series(dtype=float)
    daily = R.daily_returns(series)
    market_daily = (R.daily_returns(prices[market]) if market in prices.columns else pd.Series(dtype=float)
                    )
    return RiskMetrics(
        ticker = ticker,
        annual_return = R.annualized_return(series),
        annual_vol = _annualized_vol(daily) if len(daily) else None,
        sharpe = sharpe_ratio(daily, rf),
        sortino = sortino_ratio(daily, rf),
        max_drawdown = max_drawdown(series),
        beta = beta(daily, market_daily),
        n_days = len(daily)
    )

def risk_table(
    prices: pd.DataFrame, tickers: list[str], market: str = "SPY", rf: float | None = None
) -> pd.DataFrame:
    """A tidy table of risk metrics for the app, one row per ticker."""
    rows = []
    for t in tickers:
        m = compute_metrics(prices, t, market, rf)
        rows.append({
            "ticker": m.ticker,
            "group": config.classify(t),
            "annual_return_%": m.annual_return,
            "annual_vol_%": m.annual_vol,
            "sharpe": m.sharpe,
            "sortino": m.sortino,
            "max_drawdown_%": m.max_drawdown,
            "beta": m.beta,
        })
    return pd.DataFrame(rows).round(3)