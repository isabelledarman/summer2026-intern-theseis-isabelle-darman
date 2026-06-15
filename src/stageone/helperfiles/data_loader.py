from fredapi import Fred
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
import time

load_dotenv()

def load_all_data():
    #Fred
    fred = Fred(api_key = os.getenv('FRED_API_KEY'))
    fed_funds = fred.get_series('FEDFUNDS', observation_start = '2021-01-01')
    aerospace_ppi = fred.get_series('PCU336411336411', observation_start = '2021-01-01')
    defense = fred.get_series('FDEFX', observation_start = '2021-01-01')

    #Stock prices
    pure_play = ['RKLB', 'PL', 'IRDM', 'VSAT', 'ASTS', 'RDW', 'KTOS', 'SATL', 'LUNR']
    diversified = ['LMT', 'NOC', 'BA', 'RTX']

    all_tickers = pure_play + diversified

    prices = yf.download(all_tickers + ['SPY', 'ARKX', 'ROKT'], start = '2021-01-01')['Close']

    ##Company Financials
    financials = {}

    for t in all_tickers:
        try:
            stock = yf.Ticker(t)

            cf = stock.cashflow
            fin = stock.financials

            rev = fin.loc['Total Revenue'].sort_index()
            gp = fin.loc['Gross Profit'].sort_index()
            fcf = cf.loc['Free Cash Flow'].sort_index()

            rev.index = pd.to_datetime(rev.index)
            gp.index = pd.to_datetime(gp.index)
            fcf.index = pd.to_datetime(fcf.index)

            rev = rev[~rev.index.duplicated(keep = 'last')]
            gp = gp[~gp.index.duplicated(keep = 'last')]
            fcf = fcf[~fcf.index.duplicated(keep = 'last')]

            financials[t] = {'revenue': rev, 'gross_profit': gp, 'fcf': fcf }

        except Exception as e:
            print(f"Could not load financials for {t}: {e}")
            financials[t] = None

    return{
        'fed_funds': fed_funds,
        'aerospace_ppi' : aerospace_ppi,
        'defense': defense,
        'prices': prices,
        'financials': financials,
        'pure_play': pure_play,
        'diversified': diversified
    }
