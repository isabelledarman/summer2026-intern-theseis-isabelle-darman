from dataclasses import dataclass, field
import pandas as pd
from scipy import stats
import config
from analysis import returns as R

LOW_POWER_THRESHOLD = 20

@dataclass
class RegressionResult:
    df: pd.DataFrame
    slope: float | None = None
    intercept: float | None = None
    r_squared: float | None = None
    p_value: float | None = None
    std_err: float | None = None
    n: int = 0
    return_method: str = "annualized"
    window_start: pd.Timestamp | None = None
    window_end: pd.Timestamp | None = None
    notes: list[str] = field(default_factory = list)

    @property
    def low_power(self) -> bool:
        return self.n < LOW_POWER_THRESHOLD
    

def _revenue_growth(financials: dict, tickers: list[str]) -> dict[str, float]:
    growth = {}
    for t in tickers:
        entry = financials.get(t)
        if not entry or 'revenue' not in entry:
            continue
        g = R.total_growth(entry['revenue'])
        if g is not None:
            growth[t] = g
    return growth

def _stock_returns(prices: pd.DataFrame, tickers: list[str], method: str):
    if method == 'common':
        rets, start, end = R.common_window_return(prices, tickers)
        return rets, start, end
    rets = {}
    for t in tickers:
        if t in prices.columns:
            val = R.annualized_return(prices[t])
            if val is not None:
                rets[t] = val

    return rets, None, None

def run_regression( data, selected_tickers: list[str] | None = None, method: str = "annualized") -> RegressionResult:
    financials = data.financials
    prices = data.prices
    tickers = selected_tickers or config.ALL_TICKERS
    growth = _revenue_growth(financials, tickers)
    rets, w_start, w_end = _stock_returns(prices, tickers, method)
    valid = [t for t in tickers if t in growth and t in rets]
    df = pd.DataFrame({
        "ticker": valid,
        "revenue_growth": [growth[t] for t in valid],
        "stock_return": [rets[t] for t in valid],
        "group": [config.classify(t) for t in valid]
    })

    result = RegressionResult( df = df, n = len(df), return_method = method, window_start = w_start, window_end = w_end)

    if len(df) < 2:
        result.notes.append("Not enough valid tickers to regress")
        return result
    
    slope, intercept, r, p, se = stats.linregress(df["revenue_growth"], df["stock_return"])
    result.slope, result.intercept = slope, intercept
    result.r_squared, result.p_value, result.std_err = r ** 2, p, se
 
    if result.low_power:
        result.notes.append(
            f"n={len(df)} is small; treat the p-value as suggestive, not conclusive."
        )
    return result