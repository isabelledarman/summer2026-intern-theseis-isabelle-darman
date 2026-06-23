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
from analysis import regression, regimes, risk, robustness


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

def build_scorecard(reg, reg_div, regime, risk_df) -> list[dict]:
    signals = []
    pure = risk_df[risk_df["group"] == "pure_play"]

    spy_row = risk_df[risk_df["ticker"] == "SPY"]
    spy_ann = float(spy_row["annual_return_%"].iloc[0]) if not spy_row.empty else 13.0

    def add(name, verdict, detail, weight, kind):
        signals.append({"name": name, "verdict": verdict, "detail": detail, "weight": weight, "kind": kind})
    
    med_sharpe = pure["sharpe"].median()
    if pd.isna(med_sharpe):
        add("Pure-play Sharpe", 0, "n/a", 2, "risk")
    else:
        v = 1 if med_sharpe > 0.5 else (-1 if med_sharpe < 0 else 0)
        add("Pure-play Sharpe (median)", v, f"{med_sharpe:.2f}", 2, "risk")

    med_dd = pure["max_drawdown_%"].median()
    if pd.isna(med_dd):
        add("Pure-play drawdown", 0, "n/a", 2, "risk")
    else:
        v = 1 if med_dd > -60 else (-1 if med_dd < -80 else 0)
        add("Pure-play max drawdown (median)", v, f"{med_dd:.0f}%", 2, "risk")

    if reg.slope is None:
        add("Revenue -> return link", 0, "n/a", 1, "return")
    else:
        v = 1 if reg.slope > 0 else -1
        flag = " (low power)" if reg.low_power else ""
        add("Revenue -> return link", v, f"slope = {reg.slope}, R\u00b2={reg.r_squared:.2f}{flag}", 1, "return")

    cut_col = config.REGIME_LABELS['cutting']
    if cut_col in regime.regime_df.columns and not regime.regime_df.empty:
        cut_med = regime.regime_df[cut_col].median()
        if pd.isna(cut_med):
            add("Return in cutting era", 0, "n/a", 1, "return")
        else:
            v = 1 if cut_med > 0 else -1
            add( "Return in cutting era", v, f"{cut_med:.0f}%", 1, "return")
    else:
        add("Regime resilience", 0, "n/a", 1, "return")

    pure_ret = pure["annual_return_%"].median()

    if pd.isna(pure_ret):
        add("Pure-play return vs SPY", 0, "n/a", 1, "return")
    else:
        v = 1 if pure_ret > spy_ann else (-1 if pure_ret < 0 else 0)   
        add("Pure-play return vs SPY", v, f"{pure_ret:.0f}% vs SPY ~{spy_ann:.0f}%", 1, "return")
 
    return signals

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

    signals = build_scorecard(reg, reg_div, regime, risk_df)

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

    score = 0
    risk_score = 0
    return_score = 0
    for s in signals:
        mark = {1 : "[+] leans investable", 0 : "[~] inconclusive", -1: "[-] leans Pipe Dream"}[s["verdict"]]
        contribution = s["verdict"] * s["weight"]
        score += contribution
        if s["kind"] == "risk":
            risk_score += contribution
        else:
            return_score += s["verdict"]

        wtag = f"(x{s['weight']})" if s["weight"] > 1 else "   "
        print(f"  {wtag} {mark:28s} {s['name']}: {s['detail']}")
    
    n_decisive = sum(1 for s in signals if s["verdict"] != 0)
    if score >= 3:
        verdict = "The evidence LEANS TOWARD investable"
    elif score <= -3:
        verdict = "The evidence LEANS TOWARD pipe dream / premature"
    elif return_score > 0 and risk_score < 0:
        verdict = "Real, but too much risk"
    else:
        verdict = "The evidence is mixed"
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

    print_report(reg, reg_div, regime, risk_df, args.method, data)

    return 0

if __name__ == '__main__':
    sys.exit(main())
