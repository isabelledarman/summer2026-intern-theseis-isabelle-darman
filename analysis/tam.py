import numpy as np
import pandas as pd
import config
from analysis import returns as R
from analysis import valuation as Val

_DEFAULT_TAM = {
    "RKLB": {"tam_bn": 32},
    # Earth observation / geospatial
    "PL":   {"tam_bn": 8},
    "BKSY": {"tam_bn": 8},
    "SPIR": {"tam_bn": 4},
    # Satellite communications
    "IRDM": {"tam_bn": 6},
    "VSAT": {"tam_bn": 18},
    "ASTS": {"tam_bn": 16},
    # Space infrastructure / in-space services
    "RDW":  {"tam_bn": 5},
    "SATL": {"tam_bn": 7},
    "LUNR": {"tam_bn": 3},
    # Defense-adjacent
    "KTOS": {"tam_bn": 12},
}

def get_tam_map() -> dict:
    return getattr(config, "TAM_ESTIMATES", _DEFAULT_TAM)

def tam_penetration(data, ticker: str, target_ps: float = 4.0, years: int = 5) -> dict:
    tam_map = get_tam_map()
    out = {
        "ticker": ticker,
        "group": config.classify(ticker),
        "tam_bn": None,
        "current_rev_bn": None,
        "current_share_%": None,
        "required_rev_bn": None,
        "feasible": None,
        "note": ""
    }

    if ticker not in tam_map:
        out["note"] = "no TAM estimate for this name"
        return out
    
    info = tam_map[ticker]
    out['tam_bn'] = info['tam_bn']

    entry = data.financials.get(ticker)
    if not entry or "revenue" not in entry:
        out['note'] = 'no revenue data'
        return out
    
    rev_series = entry['revenue'].dropna().sort_index()
    if rev_series.empty:
        out['note'] = 'empty revenue series'
        return out
    
    current_rev = float(rev_series.iloc[-1])
    tam_dollars = info['tam_bn'] * 1e9
    out['current_rev_bn'] = round(current_rev / 1e9, 3)
    out['current_share_%'] = round(current_rev / tam_dollars * 100 , 2) \
        if tam_dollars > 0 else None
    
    mc = Val.current_market_cap(data, ticker)
    if mc is not None and target_ps > 0:
        required_rev = mc / target_ps
        out['required_rev_bn'] = round(required_rev/1e9, 3)
        out['required_share_%'] = round(required_rev/tam_dollars * 100, 2)\
            if tam_dollars > 0 else None
        
        if out['required_share_%'] is not None:
            out['feasible'] = out['required_share_%'] <=20
    else:
        out['note'] = 'no market cap'

    return out

def tam_table(data, ticker: list[str] | None = None, target_ps: float = 4.0, years: int = 5) -> pd.DataFrame:
    tickers = ticker or config.PURE_PLAY
    rows = [tam_penetration(data, t, target_ps, years) for t in tickers]
    df = pd.DataFrame(rows)
    for c in ["tam_bn", "current_rev_bn", "current_share_%",
              "required_rev_bn", "required_share_%"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    return df

def tam_summary(data, tickers:list[str] | None = None) -> dict:
    df = tam_table(data, tickers)
    feasible = df['feasible']
    return {
        "feasible_count": int((feasible == True).sum()),
        "stretch_count": int((feasible == False).sum()),
        "no_data_count": int(feasible.isna().sum()),
        "total": len(df),
        "median_required_share_%": round(
            float(df["required_share_%"].median()), 2)
        if df["required_share_%"].notna().any() else None,
    }