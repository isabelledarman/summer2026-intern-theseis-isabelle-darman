import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import pandas as pd
import numpy as np
import config
from data import loaders
from analysis import returns as R, regression, regimes, risk, robustness, valuation, profitability, synthesis, scorecard, dilution, tam, hurdle

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
    boot = robustness.bootstrap_regression(data)
    jack = robustness.jackknife_regression(data)
    conv = robustness.convention_robustness(data)
    drop_top = robustness.drop_top_performers(data, k=2)
    syn_stress = robustness.synthesis_stress_test(data)
    val_sens = robustness.valuation_sensitivity(data)

    return safe_json({
        "bootstrap":{
            "slope_point": boot.slope_point,
            "slope_ci": list(boot.slope_ci) if boot.slope_ci else None,
            "crosses_zero": boot.share_positive_slope,
            "share_positive": boot.share_positive_slope,
            "n_boot": boot.n_boot,
            "slope_mean": boot.slope_mean,
            "r2_point": boot.r2_point,
            "r2_mean": boot.r2_mean,
            "notes": boot.notes
        },
        "jackknife": df_to_records(jack) if isinstance(jack, pd.DataFrame) and not jack.empty else [],
        "convention": df_to_records(conv) if isinstance(conv, pd.DataFrame) else [],
        "drop_top": drop_top,
        "synthesis_stress": syn_stress,
        "valuation_sensitivity": val_sens
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
    dil_sum = dilution.dilution_summary(data)
    tam_sum = tam.tam_summary(data)
    hrd = hurdle.space_vs_benchmark(data)
    signals = scorecard.build_scorecard(reg, regime, risk_df,
                                         val_table=vt, prof_summary=prof_sum, syn_summary=syn_sum,
                                         dilution_summary=dil_sum, tam_summary=tam_sum, hurdle_result=hrd)
    verdict = scorecard.compute_verdict(signals)
    return safe_json({"signals": signals, "verdict": verdict})

@app.get("/api/dilution")
def get_dilution():
    data = get_data()
    dt = dilution.dilution_table(data)
    summary = dilution.dilution_summary(data)
    return safe_json({
        "table": df_to_records(dt),
        "summary": summary
    })
    
@app.get("/api/tam")
def get_tam():
    data= get_data()
    tt = tam.tam_table(data)
    summary = tam.tam_summary(data)
    return safe_json({
        "table": df_to_records(tt),
        "summary": summary
    })

@app.get("/api/hurdle")
def get_hurdle():
    data = get_data()
    result = hurdle.space_vs_benchmark(data, benchmark="SPY")
    return safe_json(result)

@app.get("/api/ai-context")
def get_ai_context():
    data = get_data()
    reg = regression.run_regression(data)
    risk_df = risk.risk_table(data.prices, config.ALL_TICKERS)
    vt = valuation.valuation_table(data)
    syn = synthesis.synthesis_table(data)
    prof = profitability.profitability_table(data)
    
    lines = ["Space Economy Thesis Data Snapshot", ""]

    lines.append(f"REGRESSION: slope={reg.slope}, R²={reg.r_squared}, p={reg.p_value}, n={reg.n}")
    lines.append("")
 
    pure_val = vt[vt["group"] == "pure_play"]
    lines.append("VALUATION (pure-play):")
    for _, row in pure_val.iterrows():
        lines.append(f"  {row['ticker']}: P/S={row.get('ps_ratio')}, EV/Rev={row.get('ev_to_rev')}, "
                     f"impliedCAGR={row.get('implied_required_cagr_%')}%")
    lines.append("")
 
    lines.append("SYNTHESIS (verdict per company):")
    for _, row in syn.iterrows():
        if row["group"] == "pure_play":
            lines.append(f"  {row['ticker']}: {row['verdict']} — {row.get('reason', '')}")
    lines.append("")

    lines.append("PROFITABILITY:")
    for _, row in prof.iterrows():
        if row["group"] == "pure_play":
            lines.append(f"  {row['ticker']}: GM={row.get('gross_margin_%')}%, "
                         f"improving={row.get('margin_improving')}, "
                         f"FCF+={row.get('fcf_positive')}, "
                         f"runway={row.get('runway_years')}yr")
 
    return {"context": "\n".join(lines)}

@app.post("/api/ai-analyze")
async def ai_analyze(request: Request):
    """Proxy AI requests to Anthropic API to avoid browser CORS issues."""
    body = await request.json()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set in environment"}
 
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": body.get("model", "claude-sonnet-4-6"),
                "max_tokens": body.get("max_tokens", 1000),
                "messages": body.get("messages", []),
            },
        )
        return resp.json()
 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port = 8000)