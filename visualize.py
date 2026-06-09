from fredapi import Fred
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
import time

load_dotenv()
fred = Fred(api_key = os.getenv('FRED_API_KEY'))

fed_funds = fred.get_series('FEDFUNDS', observation_starts = '2010-01-01')
aerospace_ppi = fred.get_series('PCU336411336411', observation_start='2010-01-01')
defense = fred.get_series('FDEFX', observation_start='2010-01-01')

tickers = ['RKLB', 'PL', 'IRDM', 'VSAT']
revenues = {}
fcfs = {}

for t in tickers:
    stock = yf.Ticker(t)
    time.sleep(2)

    financials = stock.financials
    cashflow = stock.cashflow
    revenues[t] = financials.loc['Total Revenue'].sort_index()
    fcfs[t] = cashflow.loc['Free Cash Flow'].sort_index()


prices = yf.download(tickers + ['SPY'], start = "2010-01-01")['Close']
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

##revenue
ax2 = axes[1]
colors = ['steelblue', 'coral', 'green', 'purple']
for(t, rev), color in zip(revenues.items(), colors):
    ax2.plot(rev.index, rev.values/1e9, label = t, color = color)
ax2.set_title("Annual Revenue by Company (USD Billions)")
ax2.set_ylabel("Revenue ($B)")
ax2.legend()
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}B'))

#Free Cash Flow
ax3 = axes[2]
for(t, fcf), color in zip(fcfs.items(), colors):
    ax3.plot(fcf.index, fcf.values/1e9, label = t, color = color)
ax3.set_title("Free Cash Flow by Company (USD Billions)")
ax3.set_ylabel("FCF ($B)")
ax3.legend()
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}B'))

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
ax4.legend()

#Formatting
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('plots')
plt.show