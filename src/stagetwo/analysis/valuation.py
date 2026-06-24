import numpy as np
import pandas as pd
import config
from analysis import returns as R

def _latest(series: pd.Series) -> float | None:
    s = series.dropna().sort_index()
    return float(s.iloc[-1]) if len(s) else None

def _market_cap_series(price: pd.Series, shares: pd.Series) -> pd.Series | None:
    s = shares.dropna().sort_index()
    if s.empty:
        return None
    aligned = (s.reindex(price.index.union(s.index)).sort_index().ffill().reindex(price.index))
    mc = (aligned * price).dropna()
    return mc if not mc.empty else None

def _revnue_ffilled(revenue: pd.Series, index: pd.Index) -> pd.Series | None:
    r = revenue.dropna().sort_index()
    if r.empty:
        return None
    return (r.reindex(index.union(r.index)).sort_index().ffill().reindex(index))

def current_market_cap(data, ticker: str) -> float | None:
    if ticker not in data.prices.columns:
        return None
    entry = data.financials.get(ticker)
    if not entry or "shares" not in entry:
        return None
    price = _latest(data.prices[ticker])
    shares = _latest(entry['shares'])
    if price is None or shares is None:
        return None
    return price * shares

#Price to Sales
def ps_ratio(data, ticker: str) -> float | None:
    mc = current_market_cap(data, ticker)
    entry = data.financials.get(ticker)
    if mc is None or not entry or 'revenue' not in entry:
        return None
    rev = _latest(entry['revenue'])
    if not rev or rev <= 0:
        return None
    return mc/rev

def ps_series(data, ticker: str) -> pd.Series | None:
    if ticker not in data.prices.columns:
        return None
    entry = data.financials.get(ticker)
    if not entry or "shares" not in entry or "revenue" not in entry:
        return None
    price = data.prices[ticker].dropna()
    mc = _market_cap_series(price, entry['shares'])
    if mc is None:
        return None
    rev = _revnue_ffilled(entry['revenue'], mc.index)
    if rev is None: 
        return None
    ps = (mc / rev).replace([np.inf, -np.inf], np.nan).dropna()
    return ps if not ps.empty else None

def ev_to_revenue(data, ticker: str) -> float | None:
    entry = data.financials.get(ticker)
    mc = current_market_cap(data, ticker)
    if mc is None or not entry or 'revenue' not in entry:
        return None
    if 'debt' not in entry and 'cash' not in entry:
        return None
    debt = _latest(entry['debt']) if 'debt' in entry else 0.0
    cash = _latest(entry['cash']) if 'cash' in entry else 0.0
    rev = _latest(entry['revenue'])
    if not rev or rev <= 0:
        return None
    ev = mc + (debt or 0.0) - (cash or 0.0)
    return ev/rev

def implied_required_cagr(data, ticker: str, target_ps: float = 4.0, years: int = 5) -> float | None:
    ps = ps_ratio(data, ticker)
    if ps is None or ps <= 0:
        return None
    if ps <= target_ps:
        return 0.0
    return ((ps/target_ps) ** (1/years) - 1) * 100.0

def decompose_return(data, ticker: str) -> dict:
    out = {"ticker": ticker, "total_return_%": None, "fundamental_%": None, "rerating_%": None, "note": ""}
    if ticker not in data.prices.columns:
        out["note"] = "no price data"
        return out
    entry = data.financials.get(ticker)
    if not entry or "shares" not in entry or "revenue" not in entry:
        out["note"] = "missing shares/revenue"
        return out
    
    price = data.prices[ticker].dropna()
    rev = entry['revenue'].dropna().sort_index()
    shares = entry['shares'].dropna().sort_index()
    if len(price) < 2 or len(rev) < 2 or shares.empty:
        out["note"] = "insufficient history"
        return out
    
    def nearest(series, when):
        s = series.dropna().sort_index()
       
        idx = s.index.get_indexer([when], method="nearest")[0]
        return float(s.iloc[idx])
    
    t0, t1 = rev.index[0], rev.index[-1]
    rev0, rev1 = float(rev.iloc[0]), float(rev.iloc[-1])
    sh0, sh1 = nearest(shares, t0), nearest(shares, t1)
    px0, px1 = nearest(price, t0), nearest(price, t1)
    if min(rev0, sh0, px0) <= 0:
        out['note'] = 'non-positive anchor'
        return out
    
    sps0, sps1 = rev0 /sh0, rev1 / sh1
    ps0, ps1 = (px0 * sh0) / rev0, (px1 * sh1) / rev1

    out['total_return_%'] = (px1/px0 - 1) * 100
    out['fundamental_%'] = (sps1 / sps0 - 1) * 100
    out['rerating_%'] = (ps1 / ps0 - 1) * 100
    return out

def valuation_table(data, tickers: list[str] | None = None, target_ps: float = 4.0, years: int = 5):
    tickers = tickers or config.ALL_TICKERS
    rows = []
    for t in tickers:
        entry = data.financials.get(t)
        rev_growth = None
        if entry and 'revenue' in entry:
            rev_growth = R.total_growth(entry['revenue'])
        ps = ps_ratio(data, t)
        rows.append({
            "ticker": t,
            "group": config.classify(t),
            "market_cap": current_market_cap(data, t),
            "ps_ratio": ps,
            "ev_to_rev": ev_to_revenue(data, t),
            "rev_growth_%": rev_growth,
            "ps_to_growth": (ps/rev_growth if (ps and rev_growth and rev_growth >0) else None),
            "implied_required_cagr_%": implied_required_cagr(data, t, target_ps, years),
        })

    df = pd.DataFrame(rows)
    for c in ['market_cap', 'ps_ratio', 'ev_to_rev', 'rev_growth_%', 'ps_to_growth', 'implied_required_cagr_%']:
        df[c] = pd.to_numeric(df[c], errors = 'coerce').round(2)

    return df
        
def decomposition_table(data, tickers: list[str] | None = None) -> pd.DataFrame:
    tickers = tickers or config.ALL_TICKERS
    rows = [decompose_return(data, t) for t in tickers]
    df = pd.DataFrame(rows)
    df['group'] = [config.classify(t) for t in df['ticker']]
    for c in ['total_return_%', 'fundamental_%', 'rerating_%']:
        df[c] = pd.to_numeric(df[c], errors='coerce').round(1)
    return df