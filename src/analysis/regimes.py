from dataclasses import dataclass, field
import pandas as pd
from scipy import stats
import config
from analysis import returns as R

def _high_cutoff() -> str:
    return getattr(config, "REGIME_HIGH_CUTOFF", getattr(config, "REGIME_LOW_HIGh_CUTOFF", '2022-03-01'))

def _cut_cutoff()->str:
    return getattr(config, "REGIME_LOW_CUTOFF", getattr(config, "REGIME_HIGH_CUT_CUTOFF", '2024-09-01'))   

@dataclass
class RegimeResult:
    regime_df: pd.DataFrame
    normalized: pd.DataFrame
    space_index: pd.Series | None = None
    spy: pd.Series | None = None
    t_stat: float | None = None
    p_value: float | None = None
    notes: list[str] = field(default_factory=list)

def _period_return(df: pd.DataFrame, tickers: list[str]) -> dict[str, float]:
    out = {}
    for t in tickers:
        if t in df.columns:
            clean = df[t].dropna()
            if len(clean) >= 2:
                out[t] = (clean.iloc[-1] - clean.iloc[0]) / clean.iloc[0] * 100
    return out

def run_regime_analysis(
    data, selected_tickers: list[str] | None = None
) -> RegimeResult:
    prices = data.prices
    tickers = selected_tickers or config.ALL_TICKERS
 
    normalized = R.normalize_to_base(prices)
    high_cut, low_cut = _high_cutoff(), _cut_cutoff()
 
    in_scope = [t for t in tickers if t in normalized.columns]
 
    low = normalized[normalized.index < high_cut]
    high = normalized[(normalized.index >= high_cut) & (normalized.index < low_cut)]
    cutting = normalized[normalized.index >= low_cut]
 
    low_r = _period_return(low, in_scope)
    high_r = _period_return(high, in_scope)
    cut_r = _period_return(cutting, in_scope)
 
    labels = config.REGIME_LABELS
    regime_df = pd.DataFrame({
        labels["low"]: pd.Series(low_r),
        labels["high"]: pd.Series(high_r),
        labels["cutting"]: pd.Series(cut_r),
    }).dropna(thresh=2)
 
    result = RegimeResult(regime_df=regime_df, normalized=normalized)
 
    # t-test: low-rate vs high-rate return distributions.
    lo, hi = list(low_r.values()), list(high_r.values())
    if len(lo) >= 2 and len(hi) >= 2:
        result.t_stat, result.p_value = stats.ttest_ind(lo, hi)
    else:
        result.notes.append("Too few tickers in a regime to run the t-test.")
 
    # Equal-weighted space index (selected names only) + SPY for the chart.
    if in_scope:
        result.space_index = normalized[in_scope].mean(axis=1)
    if "SPY" in normalized.columns:
        result.spy = normalized["SPY"]
 
    return result
 