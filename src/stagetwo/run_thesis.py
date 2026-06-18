import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import config
from data.loaders import load_market_data
from analysis import regression, regimes, risk

OUTPUT_DIR = "output"

def chart_regression(result: regression.RegressionResult, path: str) -> None:
    df = result.df
    if df.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = {'pure_play': 'steelblue', 'diversified': 'gray'}
    
    for _, row in df.iterrows():
        ax.scatter(row['revenue_growth'], row['stock_return'], color=colors.get(row['group'], "black"), s = 150, zorder = 5)
        ax.annotate(row['ticker'], 
                    (row['revenue_growth'], row['stock_return']),
                    xytext =(8, 4), textcoords='offset points',
                    fontsize=12, fontweight='bold')

    if result.slope is not None:
        x = np.linspace(df['revenue_growth'].min() - 20, df['revenue_growth'].max() + 20, 100)
        y = result.slope * x + result.intercept
        ax.plot(x, y, color = 'black', linestyle='--', linewidth = 1.5, label = f'Regression Line (R^2 = {result.r_squared ** 2: .2f})')
        ax.legend()

    ax.axhline(y=0, color='gray', linestyle = ':', linewidth = 0.8)
    ax.axvline(x = 0, color = 'gray', linestyle=':', linewidth = 0.8)
    ax.set_xlabel('Revenue Growth (%) Since 2021', fontsize=13)
    ax.set_ylabel('Stock Return (%) Since 2021', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi = 12)
    plt.close(fig)

def chart_regimes(result: regimes.RegimeResult, path: str) -> None:
    df = result.regime_df
    if df.empty:
        return
    fig, ax = plt.subplots(figsize = (14, 7))
    x = np.arange(len(df.index))
    width = 0.25
    colors = ['steelblue', 'coral', 'green']

    for i, (col, color) in enumerate(zip(df.columns, colors)):
        ax.bar(x + i * width, df[col], width, label = col, color = color, alpha = 0.85)

    ax.axhline(y = 0, color = 'black', linewidth = 0.8, linestyle = '--')
    ax.set_xticks(x + width)
    ax.set_xticklabels(df.index, fontsize = 10)
    ax.set_ylabel('Return (%)', fontsize = 12)
    ax.set_title('Space Stock Returns Across Interest Rate Regimes', fontsize = 14, fontweight = 'bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha = 0.3, axis = 'y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi = 120)
    plt.close(fig)

def chart_space_vs_spy(result: regimes.RegimeResult, path: str) -> None:
    if result.space_index is None or result.spy is None:
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(result.space_index.index, result.space_index.values,
            color='steelblue', linewidth=2, label='Space Sector (Equal Weighted)')
    ax.plot(result.spy.index, result.spy.values,
            color='black', linewidth=2, linestyle='--', label='S&P 500')

    ax.set_ylabel('Indexed Price (100 = Jan 2021)', fontsize=12)
    ax.set_title('Space Sector vs S&P 500 Across Rate Regimes', fontsize=14, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(path, dpi=12)
    plt.close(fig)

def chart_risk(risk_df: pd.DataFrame, path: str)->None:
    if risk_df.empty:
        return
    
    d = risk_df.dropna(subset=["sharpe"]).sort_values("sharpe")
    if d.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = ["steelblue" if g == "pure_play" else "gray" for g in d["group"]]
    ax.barh(d["ticker"], d["sharpe"], color=colors)
    ax.axvline(0, color="black", lw=0.8)
    ax.axvline(1, color="green", ls="--", lw=1, label="Sharpe = 1 (good)")
    ax.set_xlabel("Sharpe Ratio")
    ax.set_title("Risk-Adjusted Returns by Company")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="x")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

def build_scorecard(reg, reg_div, regime, risk_df) -> list[dict]:
    signals = []
    pure = risk_df[risk_df["group"] == "pure_play"]
    
    med_sharpe = pure["sharpe"].median()
    if pd.isna(med_sharpe):
        signals.append({"name": "Pure-play Sharpe", "verdict": 0, "detail": "insufficient data"})
    else:
        v = 1 if med_sharpe > 0.5 else (-1 if med_sharpe < 0 else 0)
        signals.append({"name": "Pure-play Sharpe (median)", "verdict": v, "detail": f"{med_sharpe:.2f}"})

    med_dd = pure["max_drawdown_%"].median()
    if pd.isna(med_dd):
        signals.append({"name": "Pure-play drawdown", "verdict": 0, "detail": "n/a"})
    else:
        v = 1 if med_dd > -60 else (-1 if med_dd < -80 else 0)
        signals.append({"name": "Pure-play ,ax drawdown (median)", "verdict": v, "detail": f"{med_dd:.0f}%"})

    if reg.slope is None:
        signals.append({"name": "Revenue -> return link", "verdict": 0, "detail": "n/a"})
    else:
        v = 1 if reg.slope > 0 else -1
        flag = " (low power)" if reg.low_power else ""
        signals.append({"name": "Revenue -> return link", "verdict": v, "detail": f"slope = {reg.slope}, R\u00b2={reg.r_squared:.2f}{flag}"})

    cut_col = config.REGIME_LABELS['cutting']
    if cut_col in regime.regime_df.columns and not regime.regime_df.empty:
        cut_med = regime.regime_df[cut_col].median()
        if pd.isna(cut_med):
            signals.append({"name": "Return in cutting era", "verdict": 0, "detail": "n/a"})
        else:
            v = 1 if cut_med > 0 else -1
            signals.append({"name": "Return in cutting era", "verdict": v, "detail": f"{cut_med:.0f}%"})
    else:
        signals.append({"name": "Regime resilience", "verdict": 0, "detail": "n/a"})

    spy_ret = None
    spy_row = risk_df[risk_df["ticker"] == "SPY"]
    pure_ret = pure["annual_return_%"].median()
    signals.append({"name": "Pure-play ann. return (median)", "verdict": 
                    (1 if (not pd.isna(pure_ret) and pure_ret > 0) else
                     (-1 if not pd.isna(pure_ret) else 0)),
                    "detail": f"{pure_ret:.0f}%" if not pd.isna(pure_ret) else "n/a"})
    
    return signals

def print_report(reg, reg_div, regime, risk_df, method) -> None:
    print("Is the space economy an investable sector?\n")
    print(f"Return convention {method} | Universe: {len(config.ALL_TICKERS)} names \n")
    
    print("Risk Adjusted Returns")
    print(risk_df.to_string(index = False))
    print()

    print(f"Regression (revenue growth -> returns)")
    print(f"slope = {reg.slope}, R\u00b2={reg.r_squared}, p = {reg.p_value}, n = {reg.n}")

    print("/nRegime T-Test (low vs high rate returns)")
    print(f" t = {regime.t_stat}, p = {regime.p_value}")

    signals = build_scorecard(reg, reg_div, regime, risk_df)
    print("\nScorecared\n")
    score = 0
    for s in signals:
        mark = {1 : "[+] leans investable", 0 : "[~] inconclusive", -1: "[-] leans Pipe Dream"}[s["verdict"]]
        score += s["verdict"]
        print(f"  {mark:28s} {s['name']}: {s['detail']}")
    
    n_decisive = sum(1 for s in signals if s["verdict"] != 0)
    if score >= 2:
        verdict = "The evidence LEANS TOWARD investable"
    elif score <= -2:
        verdict = "The evidence LEANS TOWARD pipe dream / premature"
    else:
        verdict = "The evidence is MIXED / inconclusive"
    print(f"NET SCORE: {score:+d}  ({n_decisive} decisive signals)")
    print(f"READ: {verdict}.")
    print(
        "CAVEATS: small sample (n\u2248{n}); returns measured from differing\n"
        "listing dates; thresholds in the scorecard are judgment calls, shown\n"
        "above so they can be challenged. This is a weight-of-evidence read,\n"
        "not a statistical proof.".format(n=reg.n)
    ) 



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action = "store_true", help = "bypass cache, refetch")
    ap.add_argument("--method", default="annualized", choices=["annualized", "common"], help="return convention")

    args=ap.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading market data...")
    data = load_market_data(force=args.force)

    for note in data.notes:
        print(f"   . {note}")
    if data.missing_prices:
        print(f"   ! no price data : {data.missing_prices}")
    if data.missing_financials:
        print(f"   ! no financials : {data.missing_financials}")

    tickers = config.ALL_TICKERS

    reg = regression.run_regression(data, tickers, method = args.method)
    reg_div = None
    regime = regimes.run_regime_analysis(data, tickers)
    risk_df = risk.risk_table(data.prices, tickers, market="SPY")

    chart_regression(reg, f"{OUTPUT_DIR}/1_regression.png")
    chart_risk(risk_df, f"{OUTPUT_DIR}/1_risk.png")
    chart_regimes(regime, f"{OUTPUT_DIR}/1_regimes.png")
    chart_space_vs_spy(regime, f"{OUTPUT_DIR}/1_space_vs_spy.png")

    print_report(reg, reg_div, regime, risk_df, args.method)

    return 0

if __name__ == '__main__':
    sys.exit(main())
