import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from helperfiles.data_loader import load_all_data
from matplotlib.patches import Patch
from scipy import stats
import os

def make_regression():

    data = load_all_data()
    financials = data['financials']
    prices = data['prices']
    pure_play = data['pure_play']
    diversified = data['diversified']

    all_tickers = diversified + pure_play
    tickers = [t for t in all_tickers if financials[t] is not None]

    revenue_growth = {}
    stock_returns = {}

    for t in tickers:
        rev = financials[t]['revenue'].copy()
        rev_clean = rev.dropna()
        if len(rev_clean) < 2:
            continue

        growth = (rev_clean.iloc[-1] - rev_clean.iloc[0])/abs(rev_clean.iloc[0]) * 100
        revenue_growth[t] = growth

        if t in prices.columns:
            start = prices[t].dropna().iloc[0]
            end = prices[t].dropna().iloc[-1]
            ret = (end - start) / start *100
            stock_returns[t] = ret

    valid_tickers = [t for t in tickers if t in revenue_growth and t in stock_returns]

    df = pd.DataFrame({
        'ticker': valid_tickers,
        'revenue_growth': [revenue_growth[t] for t in valid_tickers],
        'stock_return': [stock_returns[t] for t in valid_tickers],
        'group': ['pure_play' if t in pure_play else 'diversified' for t in valid_tickers]
    })

    print(df)

    #Regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['revenue_growth'],
        df['stock_return']
    )

    print(f"\nR2 = {r_value ** 2: 3f}")
    print(f"\nSlope: {slope: .3f}")
    print(f"P-value: {p_value: .3f}")

    #chart
    fig, ax = plt.subplots(figsize=(10, 7))
    group_colors = {'pure_play': 'steelblue', 'diversified': 'gray'}
    
    for _, row in df.iterrows():
        ax.scatter(row['revenue_growth'], row['stock_return'], color=group_colors[row['group']], s = 150, zorder = 5)
        ax.annotate(row['ticker'], 
                    xy=(row['revenue_growth'], row['stock_return']),
                    xytext =(8, 4), textcoords='offset points',
                    fontsize=12, fontweight='bold')

    x_line = np.linspace(df['revenue_growth'].min() - 20, df['revenue_growth'].max() + 20, 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color = 'black', linestyle='--', linewidth = 1.5, label = f'Regression Line (R^2 = {r_value ** 2: .2f})')

    ax.axhline(y=0, color='gray', linestyle = ':', linewidth = 0.8)
    ax.axvline(x = 0, color = 'gray', linestyle=':', linewidth = 0.8)

    legend_elements = [
        Patch(facecolor='steelblue', label = 'Pure-play space'),
        Patch(facecolor='gray', label='Diversified aerospace')
    ]

    ax.legend(handles = legend_elements + ax.get_legend_handles_labels()[0], fontsize=10)
    ax.set_xlabel('Revenue Growth (%) Since 2021', fontsize=13)
    ax.set_ylabel('Stock Return (%) Since 2021', fontsize=13)

    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    chart_dir = os.path.join(os.path.dirname(__file__), '..', 'charts')
    plt.savefig(os.path.join(chart_dir, 'regression_plots.png'))

    return{
        'r_squared': round(r_value ** 2, 3),
        'p_value': round(p_value, 3),
        'n': len(df)
    }

def main():
    make_regression()

if __name__ == '__main__':
    main()