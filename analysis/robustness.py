from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats
import config
from analysis import regression as Reg
from analysis import regimes as Regm
from analysis import synthesis as Syn
from analysis import valuation as Val

@dataclass
class BootstrapResult:
    n_boot: int
    n_obs: int
    slope_point: float | None
    r2_point: float | None
    slope_mean: float | None = None
    slope_ci: tuple[float, float] | None = None
    r2_mean: float | None = None
    r2_ci: tuple[float, float] | None = None
    slope_crosses_zero: bool | None = None
    share_positive_slope: float | None = None
    notes: list[str] = field(default_factory=list)


def bootstrap_regression(
    data, selected_tickers: list[str] | None = None,
    method: str = "annualized", n_boot: int = 5000, seed: int = 0,
) -> BootstrapResult:
    base = Reg.run_regression(data, selected_tickers, method = method)
    df = base.df
    n = len(df)

    result = BootstrapResult(
        n_boot = n_boot, n_obs = n, slope_point = base.slope, r2_point=base.r_squared,
    )

    if n < 3:
        result.notes.append("Too few observations to bootstrap meaninfully")
        return result
    
    x = df["revenue_growth"].to_numpy()
    y = df['stock_return'].to_numpy()
    rng = np.random.default_rng(seed)

    slopes, r2s = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size = n)
        xb, yb = x[idx], y[idx]
        if np.ptp(xb) == 0:
            continue

        lr = stats.linregress(xb, yb)
        slopes.append(lr.slope)
        r2s.append(lr.rvalue ** 2)

    if not slopes:
        result.notes.append("All bootstrap samples were degenerate")
        return result
    
    slopes = np.array(slopes)
    r2s = np.array(r2s)
    lo, hi = np.percentile(slopes, [2.5, 97.5])

    result.slope_mean = float(slopes.mean())
    result.slope_ci = (float(lo), float(hi))
    result.r2_mean = float(r2s.mean())
    result.r2_ci = tuple(float(v) for v in np.percentile(r2s, [2.5, 97.5]))
    result.slope_crosses_zero = bool(lo <= 0 <= hi)
    result.share_positive_slope = float((slopes >0).mean())

    if result.slope_crosses_zero:
        result.notes.append("CI for slope corrses 0, positive relationship is not robust")
    else:
        result.notes.append("CI for slope excludes 0, relationship is reasonably stable")

    return result

def jackknife_regression(data, selected_tickers: list[str] | None = None, method: str = "annualized",
                         )-> pd.DataFrame:
    base = Reg.run_regression(data, selected_tickers, method=method)
    df = base.df
    if len(df) < 4 or base.slope is None:
        return pd.DataFrame()
    
    rows = []
    for t in df["ticker"]:
        sub = df[df["ticker"] != t]
        lr = stats.linregress(sub['revenue_growth'] , sub['stock_return'])
        rows.append({
            "dropped": t,
            "slope_without": lr.slope,
            "r2_without": lr.rvalue **2,
            "slope_change": lr.slope - base.slope,
            "r2_change": (lr.rvalue ** 2) - base.r_squared
        })

    out = pd.DataFrame(rows)
    out['abs_slope_change'] = out["slope_change"].abs()
    return out.sort_values("abs_slope_change", ascending= False).round(4)

def drop_top_performers(data, k: int = 2, selected_tickers: list[str] | None = None, method: str = "annualized"
                        )->dict:
    base = Reg.run_regression(data, selected_tickers, method=method)
    df = base.df
    if len(df) < k + 3:
        return {"note": "Too few firms to drop top meaningfully"}
    
    top = df.nlargest(k, "stock_return")["ticker"].tolist()
    kept = df[~df["ticker"].isin(top)]
    lr = stats.linregress(kept['revenue_growth'], kept["stock_return"])

    flipped = (base.slope is not None) and (np.sign(lr.slope) != np.sign(base.slope))

    return{
        "dropped": top,
        "slope_full": base.slope,
        "slope_without_top": lr.slope,
        "r2_full": base.r_squared,
        "r2_without_top": lr.rvalue ** 2,
        "p_without_top": lr.pvalue,
        "sign_flipped": bool(flipped),
        "note": ("Slope sign flips w/o top performers, relationship driven by winners"
            if flipped else
            "Slope keeps its sign, more robust")
    }

def regime_data_sensitivity(data, selected_tickers: list[str] | None = None, high_cuts: list[str] | None = None, low_cuts: list[str] | None = None
                            )-> pd.DataFrame:
    high_cuts = high_cuts or ['2022-01-01', '2022-03-01', '2022-06-01']
    low_cuts = low_cuts or ['2024-06-01', '2024-09-01', '2024-12-01']
    high_name = "REGIME_HIGH_CUTOFF" if hasattr(config, "REGIME_HIGH_CUTOFF") \
        else "REGIME_LOW_HIGH_CUTOFF"
    low_name = "REGIME_LOW_CUTOFF" if hasattr(config, "REGIME_LOW_CUTOFF") \
        else "REGIME_HIGH_CUT_CUTOFF"
    
    had_high = hasattr(config, high_name)
    had_low = hasattr(config, low_name)
    orig_high = getattr(config, high_name, None)
    orig_low = getattr(config, low_name, None)
    rows = []

    try:
        for hc in high_cuts:
            for lc in low_cuts:
                setattr(config, high_name, hc)
                setattr(config, low_name, lc)
                res = Regm.run_regime_analysis(data, selected_tickers)
                rows.append({
                    "high_cutoff": hc,
                    "low_cutoff": lc,
                    "t_stat": res.t_stat,
                    "p_value": res.p_value,
                    "significant_5pct": (res.p_value is not None and res.p_value < 0.05),
                })

    finally:
        if had_high:
            setattr(config, high_name, orig_high)
        elif hasattr(config, high_name):
            delattr(config, high_name)
        if had_low:
            setattr(config, low_name, orig_low)
        elif hasattr(config, low_name):
            delattr(config, low_name)

    return pd.DataFrame(rows).round(4)

def convention_robustness(data, selected_tickers: list[str] | None = None)-> pd.DataFrame:
    rows = []
    for method in ("annualized", "common"):
        r = Reg.run_regression(data, selected_tickers, method = method)
        rows.append({
            "convention": method,
            "n": r.n,
            "slope": r.slope,
            "r_squared": r.r_squared,
            "p_value": r.p_value
        })

    return pd.DataFrame(rows).round(4)

def synthesis_stress_test(data, base_threshold: float=0.5, strick_threshold: float = 0.6) -> dict:
    syn_df = Syn.synthesis_table(data, config.PURE_PLAY)
    base_counts = syn_df["verdict"].value_counts().to_dict()

    details = []
    for _, row in syn_df.itterrows():
        fs = row.get("fundamental_share")
        base_v = row["verdict"]
        strict_v = base_v
        if fs is not None and base_threshold <= fs < strick_threshold and base_v == "Earned":
            strict_v = "Mixed"
            details.append({
                "ticker": row["ticker"],
                "base_verdict": base_v,
                "strict_verdict": strict_v,
                "flipped": strict_v != base_v
            })

    return{
        "base_counts": base_counts,
        "strict_threshold": strick_threshold,
        "n_flipped": sum(1 for d in details if d["flipped"]),
        "details": details
    }

def valuation_sensitivity(data, target_base: float=4.0, target_strict: float=3.0, years: int=5) ->list[dict]:
    vt_base = Val.valuation_table(data, config.PURE_PLAY, target_ps=target_base, years=years)
    vt_strict = Val.valuation_table(data, config.PURE_PLAY, target_ps = target_strict, years = years)

    rows = []
    for _, row in vt_base.iterrows():
        strict_row = vt_strict[vt_strict['ticker'] == row['ticker']]
        strict_cagr = float(strict_row['implied_required_cagr_%'].iloc[0]) if len(strict_row) else None
        rows.append({
            "ticker": row["ticker"],
            "cagr_ps4": row.get("implied_required_cagr_%"),
            "cagr_ps3": strict_cagr
        })

    return rows