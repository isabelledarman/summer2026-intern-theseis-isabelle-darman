import numpy as np
import pandas as pd
import config
from analysis import returns as R

def share_growth(data, ticker: str) -> dict:
    entry = data.financials.get(ticker)
    if not entry or "shares" not in entry:
        return {"ticker": ticker, "share_growth_%": None, "shares_start": None, "shares_end": None, "note": "no shares data"}
    s = entry['shares'].dropna().sort_index()
    if len(s) < 2:
        return {"ticker": ticker, "share_growth_%": None, "shares_start": None, "shares_end": None, "note": "insufficient history"}
    start, end = float(s.iloc[0]), float(s.iloc[-1])
    if start <= 0:
        return {"ticker": ticker, "share_growth_%": None, "shares_start": None, "shares_end": None, "note": "non-positive anchor"}
    
    growth = (end - start) / start * 100

    return {"ticker": ticker, "share_growth_%": round(growth, 2), "shares_start": start, "shares_end": end, "note": ""}

def dilution_adjusted_return(data, ticker: str) -> dict:
    sg = share_growth(data, ticker)
    price_ret = R.annualized_return(data.prices[ticker]) if ticker in data.prices.columns else None

    out = {
        "ticker": ticker,
        "group": config.classify(ticker),
        "price_return_%": round(price_ret, 2) if price_ret is not None else None,
        "share_growth_%": sg["share_growth_%"],
        "dilution_drag_%": None,
        "dilution_adj_return_%": None,
        "heavily_dilutive": None,
        "note": sg["note"]
    }

    if price_ret is not None and sg["share_growth_%"] is not None:
        drag = sg['share_growth_%']
        out['dilution_drag_%'] = round(drag, 2)
        out['dilution_adj_return_%'] = round(price_ret - drag, 2)
        out['heavily_dilutive'] = drag > 50

    return out

def dilution_table(data, ticker: list[str] | None = None) -> pd.DataFrame:
    tickers = ticker or config.ALL_TICKERS
    rows = [dilution_adjusted_return(data, t) for t in tickers]
    df = pd.DataFrame(rows)
    for c in ["price_return_%", "share_growth_%", "dilution_drag_%",
              "dilution_adj_return_%"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    return df

def dilution_summary(data, tickers: list[str] | None = None) -> dict:
    df = dilution_table(data, tickers)
    pure = df[df['group'] == 'pure_play']
    return {
        'median_share_growth_%': round(float(pure['share_growth_%'].median()), 2)
        if pure['share_growth_%'].notna().any() else None,
        'heavily_dilutive_count': int((pure['heavily_dilutive'] == True).sum()),
        'pure_play_total': len(pure),
        'median_dilution_adj_return_%': round(
            float(pure['dilution_adj_return_%'].median()), 2)
        if pure['dilution_adj_return_%'].notna().any() else None
    }

