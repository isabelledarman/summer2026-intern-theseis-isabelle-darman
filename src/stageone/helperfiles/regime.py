import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from helperfiles.data_loader import load_all_data
from scipy import stats
import os

def make_regime():
    data = load_all_data()

    fed_funds = data['fed_funds']
    financials = data['financials']
    prices = data['prices']

    normalized = prices / prices.iloc[0] * 100

    #Regimes Based on Federal Funds Rate
    # Low Rate Era: Fed Funds < 1% (2021 - 2022)
    # High Rate Era: Fed Funds >= 1% (2022 - 2024)
    # Cutting Era: Fed funds rate falling (2024 - present)

    low_rate   = normalized[normalized.index < '2022-03-01']
    high_rate  = normalized[(normalized.index >= '2022-03-01') & (normalized.index < '2024-09-01')]
    cutting    = normalized[(normalized.index > '2024-09-01')]

    space_tickers = ['RKLB', 'PL', 'IRDM', 'VSAT', 'ASTS', 'LMT', 'NOC', 'BA', 'RTX']

    def period_return(df, tickers):
        returns = {}
        for t in tickers:
            if t in df.columns:
                clean = df[t].dropna()
                if len(clean) >= 2:
                    returns[t] = (clean.iloc[-1] - clean.iloc[0]) /clean.iloc[0] * 100

        return returns

    low_returns = period_return(low_rate, space_tickers)
    high_returns = period_return(high_rate, space_tickers)
    cut_returns = period_return(cutting, space_tickers)

    #building df
    regime_df = pd.DataFrame({
        'Low Rate Era (2021 - March 2022)': pd.Series(low_returns),
        'High Rate Era (Mar 2022 - Sep 2024)': pd.Series(high_returns),
        'Rate Cutting Era (Sep 2024 - Now)': pd.Series(cut_returns)
    })

    regime_df = regime_df.dropna(thresh = 2)

    print(regime_df.round(1))

    #T-Test: are returns different across regimes?
    low_vals = list(low_returns.values())
    high_vals = list(high_returns.values())
    t_stat, p_val = stats.ttest_ind(low_vals, high_vals)
    print(f"\nT-Stat: {t_stat: .3f}")
    print(f"\nP-value: {p_val: .3f}")

    #bar chart
    fig, ax = plt.subplots(figsize = (14, 7))
    x = np.arange(len(regime_df.index))
    width = 0.25
    colors = ['steelblue', 'coral', 'green']

    for i, (col, color) in enumerate(zip(regime_df.columns, colors)):
        ax.bar(x + 1 * width, regime_df[col], width, label = col, color = color, alpha = 0.85)

    ax.axhline(y = 0, color = 'black', linewidth = 0.8, linestyle = '--')
    ax.set_xticks(x + width)
    ax.set_xticklabels(regime_df.index, fontsize = 10)
    ax.set_ylabel('Return (%)', fontsize = 12)
    ax.set_title('Space Stock Returns Across Interest Rate Regimes', fontsize = 14, fontweight = 'bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha = 0.3, axis = 'y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('regime_bars.png', dpi = 150, bbox_inches='tight')

    #SPY vs Space index regimes

    space_index = normalized[space_tickers].mean(axis = 1)
    spy = normalized['SPY']

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.axvspan(pd.Timestamp('2021-01-01'), pd.Timestamp('2022-03-01'),
            alpha=0.15, color='green', label='Low Rate Era')
    ax.axvspan(pd.Timestamp('2022-03-01'), pd.Timestamp('2024-09-01'),
            alpha=0.15, color='red', label='High Rate Era')
    ax.axvspan(pd.Timestamp('2024-09-01'), pd.Timestamp('2026-06-01'),
            alpha=0.15, color='blue', label='Rate Cutting Era')

    ax.plot(space_index.index, space_index.values,
            color='steelblue', linewidth=2, label='Space Sector (Equal Weighted)')
    ax.plot(spy.index, spy.values,
            color='black', linewidth=2, linestyle='--', label='S&P 500')

    ax.set_ylabel('Indexed Price (100 = Jan 2021)', fontsize=12)
    ax.set_title('Space Sector vs S&P 500 Across Rate Regimes', fontsize=14, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    chart_dir = os.path.join(os.path.dirname(__file__), '..', 'charts')
    plt.savefig(os.path.join(chart_dir, 'regime_plots.png'))

    return{
        't_stat': round(t_stat, 3),
        'p_val': round(p_val, 3)
    }