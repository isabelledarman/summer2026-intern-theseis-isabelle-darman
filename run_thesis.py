import argparse
import os
import sys
from analysis import regimes, regression, risk, robustness
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import config
from data.loaders import load_market_data
from analysis import scorecard


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
        ax.plot(x, y, color = 'black', linestyle='--', linewidth = 1.5, label = f'Regression Line (R^2 = {result.r_squared: .2f})')
        ax.legend()

    ax.axhline(y=0, color='gray', linestyle = ':', linewidth = 0.8)
    ax.axvline(x = 0, color = 'gray', linestyle=':', linewidth = 0.8)
    ax.set_xlabel('Revenue Growth (%) Since 2021', fontsize=13)
    ax.set_ylabel(f'Stock Return (%, {result.return_method})', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi = 120)
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
    fig.savefig(path, dpi=120)
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

def print_report(reg, reg_div, regime, risk_df, method, data) -> None:
    print("Is the space economy an investable sector?\n")
    print(f"Return convention {method} | Universe: {len(config.ALL_TICKERS)} names \n")
    
    print("Risk Adjusted Returns")
    print(risk_df.to_string(index = False))
    print()

    print(f"Regression (revenue growth -> returns)")
    print(f"slope = {reg.slope}, R\u00b2={reg.r_squared}, p = {reg.p_value}, n = {reg.n}")

    print("\nRegime T-Test (low vs high rate returns)")
    print(f" t = {regime.t_stat}, p = {regime.p_value}")

    print("\nRobustness Checks")

    boot = robustness.bootstrap_regression(data, config.ALL_TICKERS, method=method)
    print(f" Bootstrap slope 95% CI: ({boot.slope_ci[0]: .3f}, {boot.slope_ci[1]:.3f})"
          f" | crosses zero: {boot.slope_crosses_zero}"
          f" | share positive: {boot.share_positive_slope:.0%}")
    
    top = robustness.drop_top_performers(data, k = 2, selected_tickers=config.ALL_TICKERS, method = method)
    print(f"  Drop top 2 ({top.get('dropped')}): slope {top.get('slope_full'):.3f} "
          f"-> {top.get('slope_without_top'):.3f} | {top.get('note')}")

    
    print( " Return-convention robustness")
    print(robustness.convention_robustness(data, config.ALL_TICKERS).to_string(index=False))
    print("\nScorecard\n")

    signals = scorecard.build_scorecard(reg, regime, risk_df)
    v = scorecard.compute_verdict(signals)
    
    print("\nScorecard\n")
    for s in signals:
        mark = {1: "[+] leans investable", 0: "[~] inconclusive", -1: "[-] leans Pipe Dream"}[s["verdict"]]
        wtag = f"(x{s['weight']})" if s["weight"] > 1 else "    "
        print(f"  {wtag} {mark:24s} {s['name']}: {s['detail']}")

    print(f"\nNET SCORE: {v['score']:+.0f}  ({v['n_decisive']} decisive signals)")
    print(f"  (return signals: {v['return_score']:+d}  |  risk signals: {v['risk_score']:+.0f})")
    print(f"READ: {v['verdict']}")

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

    print_report(reg, reg_div, regime, risk_df, args.method, data)

    return 0

if __name__ == '__main__':
    sys.exit(main())
