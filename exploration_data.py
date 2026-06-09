import yfinance as yf
import pandas as pd
import time

tickers = ['RKLB', 'PL', 'IRDM', 'VSAT']

for t in tickers:
    stock = yf.Ticker(t)
    time.sleep(2)

    financials = stock.financials
    cashflow = stock.cashflow

    print(f"\n---- {t} ---")
    print(financials.loc['Total Revenue'])
    print(financials.loc['Gross Profit'])
    print(cashflow.loc['Free Cash Flow'])
