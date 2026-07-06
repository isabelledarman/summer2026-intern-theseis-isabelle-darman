import numpy as np
import pandas as pd
import config

def _get(entry: dict | None, *keys: str) -> pd.Series | None:
    if not entry:
        return None
    for k in keys:
        if k in entry:
            return entry[k]
        
    return None

def _latest(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    s = series.dropna().sort_index()
    return float(s.iloc[-1]) if len(s) else None

def gross_margin_series(data, ticker: str) -> pd.Series | None:
    entry = data.financials.get(ticker)
    rev = _get(entry, 'revenue')
    gp = _get(entry, 'gross_profit', 'gross profit')
    if rev is None or gp is None:
        return None
    rev = rev.dropna().sort_index()
    gp = gp.dropna().sort_index()

    joined = pd.concat([gp, rev], axis = 1, join = 'inner').dropna()
    if joined.empty:
        return None
    
    margin = (joined.iloc[:, 0]/joined.iloc[:, 1] * 100)
    margin = margin.replace([np.inf, -np.inf], np.nan).dropna()
    return margin if not margin.empty else None

def gross_margin_trend(data, ticker: str) -> dict:
    out = {"latest_%": None, "earliest_%": None, "change_pp": None, "improving": None}
    m = gross_margin_series(data, ticker)
    if m is None or m.empty:
        return out
    
    out['latest_%'] = float(m.iloc[-1])
    out["earliest_%"] = float(m.iloc[0])
    if len(m) >= 2:
        out["change_pp"] = float(m.iloc[-1] - m.iloc[0])
        out['improving'] = out['change_pp'] > 0

    return out

def burn_and_runway(data, ticker: str) -> dict:
    entry = data.financials.get(ticker)
    out = {'latest_fcf': None, "fcf_positive": None, "annual_burn": None, "cash": None, "runway_years": None, "runway_quarters": None, "note": ""}

    fcf = _get(entry, 'fcf')
    if fcf is not None:
        f = fcf.dropna().sort_index()
        if len(f):
            latest = float(f.iloc[-1])
            out['latest_fcf'] = latest
            out['fcf_positive'] = latest > 0
            out['annual_burn'] = abs(latest) if latest < 0 else 0.0

    cash = _latest(_get(entry, 'cash'))
    out['cash'] = cash
    burn = out['annual_burn']

    if cash is None:
        out['note'] = "No cash data loaded"
    elif not burn or burn <= 0:
        out["note"] - "cash-generative"
    else:
        years = cash/burn
        out['runway_years'] = years
        out['runway_quarters'] = years *4

    return out

def profitability_table(data, tickers: list[str] | None = None) -> pd.DataFrame:
    tickers = tickers or config.ALL_TICKERS
    rows = []

    for t in tickers:
        gm = gross_margin_trend(data, t)
        br = burn_and_runway(data, t)

        rows.append({
            "ticker": t,
            "group": config.classify(t),
            "gross_margin_%": gm['latest_%'],
            "margin_change_pp": gm["change_pp"],
            "margin_improving": gm["improving"],
            "fcf_positive": br["fcf_positive"],
            "annual_burn": br["annual_burn"],
            "cash": br["cash"],
            "runway_years": br["runway_years"]
        })

    df = pd.DataFrame(rows)

    for c in ["gross_margin_%", "margin_change_pp", "annual_burn", "cash", "runway_years"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").round(2)

    return df

def profitability_summary(data, tickers: list[str] | None = None) -> dict:
    df = profitability_table(data, tickers)
    pure = df[df["group"] == "pure_play"]

    return{
        "margins_improving": int((pure["margin_improving"] == True).sum()),
        "margins_deteriorating": int((pure["margin_improving"] == False).sum()),
        "cash_positive": int((pure["fcf_positive"] == True).sum()),        
        "burning_cash": int((pure["fcf_positive"] == False).sum()),
        "pure_play_total": int(len(pure))
    }