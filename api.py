import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import config
from data import loaders
from analysis import returns as R, regression, regimes, risk, robustness, valuation, profitability, synthesis, scorecard

app = FastAPI(title = "Space Economy Thesis API")
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

_data = None
def get_data():
    global _data
    if _data is None:
        _data = loaders.load_market_data()
    return _data

def safe_json(obj):
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj

def df_to_records(df: pd.DataFrame)->list[dict]:
    return safe_json(df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict("records"))

@app.get("/api/config")
def get_config():
    return{
        "pure_play": config.PURE_PLAY,
        "diversified": config.DIVERSIFIED,
        "benchmarks": config.BENCHMARKS,
        "start_data": config.START_DATE
    }

@app.get("/api/returns")
def get_returns():
    data = get_data()
    tickers = config.ALL_TICKERS + config.BENCHMARKS
    rows = []
    for t in tickers:
        if t not in data.prices.columns:
            continue
        s = data.prices[t].dropna()
        if len(s) < 2:
            continue
        ann = R.annualized_return(s)
        tot = R.simple_return(s)
        rows.append({"ticker": t, "group": config.classify(t), "annualized_return": ann, "total_return": tot})
    return rows

@app.get("/api/prices")
def get_prices():
    data = get_data()
    cols = [t for t in config.ALL_TICKERS + config.BENCHMARKS if t in data.prices.columns]
    df = data.prices[cols].dropna(how='all').resample('M').last()
    first = df.iloc[0]
    rebased = (df/first * 100).round(2)
    records = []
    for idx, row in rebased.iterrows():
        r = {"month": idx.strftime("%Y-%m")}
        for c in cols:
            r[c] = None if pd.isna(row[c]) else round(row[c], 1)
        records.append(r)
    return records

@app.get("/api/regression")
def get_regression():
    data = get_data()
    reg = regression.run_regression(data)
    result = {

        "slope": reg.slope,
        "intercept": reg.intercept,
        "r_squared": reg.r_squared,
        "p_value": reg.p_value,
        "n": reg.n,
        "low_power": reg.low_power,
        "points": [{"ticker": row["ticker"], "revenue_growth": row["revenue_growth"], "stock_return": row["stock_return"], "group":row['group']} for _, row in reg.df.iterrows()]
    }
    return safe_json(result)

@app.get("/api/risk")
def get_risk():
    data = get_data()
    df = risk.risk_table(data.prices, config.ALL_TICKERS)
    return df_to_records(df)

@app.get("/api/regimes")
def get_regimes():
    data = get_data()
    reg = regimes.run_regime_analysis(data)
    return df_to_records(reg.regime_df)

@app.get("/api/robustness")
def get_robustness():
    data = get_data()
    reg = robustness.bootstrap_regression(data)
    boot = robustness.bootstrap_regression(data)
    jack = robustness.jackknife_regression(data)
    conv = robustness.convention_robustness(data)
    return safe_json({
        "bootstrap":{
            "slope_point": boot.slope_point,
            "slope_ci": list(boot.slope_ci) if boot.slope_ci else None,
            "crosses_zero": boot.slope_crosses_zero,
            "share_positive": boot.share_positive_slope,
            "n_boot": boot.n_boot,
        },
        "jackknife": df_to_records(jack) if isinstance(jack, pd.DataFrame) and not jack.empty else [],
        "convention": df_to_records(conv) if isinstance(conv, pd.DataFrame) else []
    })

@app.get("/api/valuation")
def get_valuation():
    data = get_data()
    vt = valuation.valuation_table(data)
    dt = valuation.decomposition_table(data)
    return{
        "valuation": df_to_records(vt),
        "decomposition": df_to_records(dt)
    }

@app.get("/api/profitability")
def get_profitability():
    data = get_data()
    rows = profitability.profitability_table(data)
    return safe_json(rows) if isinstance(rows, list) else df_to_records(rows)

@app.get("/api/synthesis")
def get_synthesis():
    data = get_data()
    syn = synthesis.synthesis_table(data)
    return df_to_records(syn) if isinstance(syn, pd.DataFrame) else safe_json(syn)

@app.get("/api/scorecard")
def get_scorecard():
    data = get_data()
    reg = regression.run_regression(data)
    regime = regimes.run_regime_analysis(data)
    risk_df = risk.risk_table(data.prices, config.ALL_TICKERS)
    vt = valuation.valuation_table(data)
    prof_sum = profitability.profitability_summary(data)
    syn_sum = synthesis.synthesis_summary(data)

    signals = scorecard.build_scorecard(reg, regime, risk_df,
                                         val_table=vt, prof_summary=prof_sum, syn_summary=syn_sum)
    verdict = scorecard.compute_verdict(signals)
    return safe_json({"signals": signals, "verdict": verdict})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port = 8000)