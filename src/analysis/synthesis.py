import numpy as np
import pandas as pd
import config
from analysis import valuation as val
from analysis import profitability as prof

FUNDAMENTAL_SHARE_STRONG = 0.5
FUNDAMENTAL_SHARE_SOME = 0.2

def _fundamental_share(fundamental_pct: float, rerating_pct: float) -> float | None:
    f = fundamental_pct / 100.0
    r = rerating_pct / 100.0
    if f <= -1 or r <= -1:
        return None
    lf, lr = np.log1p(f), np.log1p(r)
    denom = abs(lf) + abs(lr)
    if denom == 0:
        return None
    return abs(lf) / denom

def classify_company(data, ticker: str) -> dict:
    dec = val.decompose_return(data, ticker)
    gm = prof.gross_margin_trend(data, ticker)
    br = prof.burn_and_runway(data, ticker)

    out = {
        "ticker": ticker,
        "group": config.classify(ticker),
        "total_return_%": dec.get("total_return_%"),
        "fundamental_%": dec.get("fundamental_%"),
        "rerating_%": dec.get("rerating_%"),
        "fundamental_share": None,
        "margin_improving": gm.get("improving"),
        "fcf_positive": br.get("fcf_positive"),
        "runway_years": br.get("runway_years"),
        "verdict": "insufficient data",
        "reason": "",
    }

    f, r = dec.get("fundamental_%"), dec.get("rerating_%")
    if f is None or r is None:
        out['reason'] = dec.get('note') or 'no decomposition'
        return out
    
    share = _fundamental_share(f, r)
    out['fundamental_share'] = None if share is None else round(share, 2)

    progressing = (gm.get('improving') is True) or (br.get('fcf_positive') is True)

    if share is None:
        out['verdict'] = 'insufficient data'
        out['reason'] = 'return legs too small to decompose'
    elif share >= FUNDAMENTAL_SHARE_STRONG and progressing:
        out['verdict'] = 'Earned'
        out['reason'] = ("returns mostly fundamental and the business is progessing (margins up or cash-generative)")
    elif share >= FUNDAMENTAL_SHARE_STRONG and not progressing:
        out['verdict'] = 'Mixed'
        out['reason'] = ('returns are fundamental but operating progress is weak (margins not improving, still burning)')
    elif share >= FUNDAMENTAL_SHARE_SOME and progressing:
        out['verdict'] = 'Mixed'
        out['reason'] = 'partial fundamental support with some operating progress'
    else:
        out['verdict'] = 'Narrative'
        out['reason'] = 'returns came mostly from multiple re-rating with weak fundamental/operating support'

    return out

def synthesis_table(data, tickers: list[str] | None = None) -> pd.DataFrame:
    tickers = tickers or config.ALL_TICKERS
    rows = [classify_company(data, t) for t in tickers]
    df = pd.DataFrame(rows)
    for c in ['total_return_%', 'fundamental_%', 'rerating_%']:
        df[c] = pd.to_numeric(df[c], errors = 'coerce').round(1)
    return df

def synthesis_summary(data, tickers: list[str] | None = None) -> dict:
    df = synthesis_table(data, tickers)
    pure = df[df['group'] == 'pure_play']
    counts = pure['verdict'].value_counts().to_dict()
    return{
        'earned': int(counts.get("Earned", 0)),
        'narrative': int(counts.get("Narrative", 0)),
        'mixed': int(counts.get("Mixed", 0)),
        'insufficient': int(counts.get('Insufficient Data', 0)),
        'pure_play_total': int(len(pure))
    }