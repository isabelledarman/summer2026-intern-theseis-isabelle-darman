import numpy as np
import pandas as pd
import config
from analysis import returns as R
from analysis import risk as rk
 
 
def space_vs_benchmark(data, benchmark: str = "SPY") -> dict:
    prices = data.prices
    pure_metrics = []
    for t in config.PURE_PLAY:
        m = rk.compute_metrics(prices, t, benchmark)
        if m.sharpe is not None:
            pure_metrics.append({
                "ticker": t,
                "sharpe": m.sharpe,
                "sortino": m.sortino,
                "annual_return_%": m.annual_return,
                "annual_vol_%": m.annual_vol,
                "max_drawdown_%": m.max_drawdown,
                "beta": m.beta,
            })
 
    if not pure_metrics:
        return {"note": "no valid pure-play metrics"}
 
    pdf = pd.DataFrame(pure_metrics)
 
    # Benchmark metrics
    bm = rk.compute_metrics(prices, benchmark, benchmark)
 
    space_med_sharpe = float(pdf["sharpe"].median())
    space_med_sortino = float(pdf["sortino"].median()) if pdf["sortino"].notna().any() else None
    space_med_ret = float(pdf["annual_return_%"].median())
    space_med_vol = float(pdf["annual_vol_%"].median()) if pdf["annual_vol_%"].notna().any() else None
    space_med_dd = float(pdf["max_drawdown_%"].median())
 
    sharpe_premium = space_med_sharpe - (bm.sharpe or 0)
    return_premium = space_med_ret - (bm.annual_return or 0)
 
    # Verdict
    if sharpe_premium > 0.1:
        verdict = "POSITIVE — space offers better risk-adjusted returns"
    elif sharpe_premium > -0.1:
        verdict = "NEUTRAL — space premium is negligible"
    else:
        verdict = "NEGATIVE — space does not compensate for extra risk"
 
    compensated = sharpe_premium > 0
 
    return {
        "space_median_sharpe": round(space_med_sharpe, 3),
        "space_median_sortino": round(space_med_sortino, 3) if space_med_sortino else None,
        "space_median_return_%": round(space_med_ret, 2),
        "space_median_vol_%": round(space_med_vol, 2) if space_med_vol else None,
        "space_median_drawdown_%": round(space_med_dd, 2),
        "benchmark": benchmark,
        "benchmark_sharpe": round(bm.sharpe, 3) if bm.sharpe else None,
        "benchmark_return_%": round(bm.annual_return, 2) if bm.annual_return else None,
        "sharpe_premium": round(sharpe_premium, 3),
        "return_premium_%": round(return_premium, 2),
        "compensated": compensated,
        "verdict": verdict,
        "per_name": pure_metrics,
    }
 
