import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from helperfiles.data_loader import load_all_data
import os

def make_initial_charts():
    data = load_all_data()

    fed_funds = data['fed_funds']
    prices = data['prices']
    financials = data['financials']
    aerospace_ppi = data['aerospace_ppi']

    tickers = ['RKLB', 'PL', 'IRDM', 'VSAT']
    revenues = {}
    fcfs = {}

    for t in tickers:
        rev = financials[t]['revenue'].copy()
        fcf = financials[t]['fcf'].copy()
        rev.index = rev.index.year
        fcf.index = fcf.index.year
        rev = rev[~rev.index.duplicated(keep = 'last')]
        fcf = fcf[~fcf.index.duplicated(keep = 'last')]
        revenues[t] = rev
        fcfs[t] = fcf

    normalized = prices/prices.iloc[0] * 100

    fig, axes = plt.subplots(4, 1, figsize = (14, 20))
    fig.suptitle('Space Economy: Investment Thesis Data', fontsize = 16, fontweight = 'bold')


    #fed funds and aerospace ppi
    ax1 = axes[0]
    ax1b = ax1.twinx()
    ax1.plot(fed_funds.index, fed_funds.values, color = 'steelblue', label = 'Fed Funds Rate (%)')
    ax1b.plot(aerospace_ppi.index, aerospace_ppi.values, color = 'coral', label = 'Aerospace PPI')
    ax1.set_title('Interest Rate vs Aerospace Input Costs')
    ax1.set_ylabel('Federal Funds Rate (%)')
    ax1b.set_ylabel('Aerospace PPI')
    ax1.legend(loc = 'upper left')
    ax1b.legend(loc = 'upper right')

    #Rates rose but input cost kept rising, rising costs and rates squeezed cos from both sides

    ##revenue
    ax2 = axes[1]
    colors = ['steelblue', 'coral', 'green', 'purple']
    for(t, rev), color in zip(revenues.items(), colors):
        ax2.plot(rev.index, rev.values/1e9, label = t, color = color)
    ax2.set_title("Annual Revenue by Company (USD Billions)")
    ax2.set_ylabel("Revenue ($B)")
    ax2.legend()
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: str(int(x))))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}B'))


    #VSAT dominates, RKLB grew fas from 0 while RDM shows steady stable growth
    #RKLB and PL are still small compared to legacy firms -> new space revenue base is still small 

    #Free Cash Flow
    ax3 = axes[2]
    for(t, fcf), color in zip(fcfs.items(), colors):
        ax3.plot(fcf.index, fcf.values/1e9, label = t, color = color)
    ax3.set_title("Free Cash Flow by Company (USD Billions)")
    ax3.set_ylabel("FCF ($B)")
    ax3.legend()
    ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: str(int(x))))
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}B'))

    #IRDM is consistently positive, VSAT crashed then recovered RKLB is getting worse, PL just became positive
    #Only one company is reliably cash flow positive

    #performance vs s and p 500
    ax4 = axes[3]
    for col in normalized.columns:
        if col == 'SPY':
            ax4.plot(normalized.index, normalized[col], color='black', 
                    linewidth=2, linestyle='--', label='S&P 500')
        else:
            ax4.plot(normalized.index, normalized[col], label = col)
    ax4.set_title("Stock Performance vs S&P 500 Performance (normalized)")
    ax4.set_ylabel('Indexed Price')
    ax4.set_ylim(0, 400)
    ax4.legend()

    #Most underperformedperformed SPY

    #Formatting
    for ax in [ax1, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()

    chart_dir = os.path.join(os.path.dirname(__file__), '..', 'charts')
    plt.savefig(os.path.join(chart_dir, 'initial_plots.png'))