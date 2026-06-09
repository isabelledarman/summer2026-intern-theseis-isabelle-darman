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
    space_tickers = ['RKLB', 'PL', 'IRDM', 'VSAT', 'LMT', 'NOC', 'ARKX', 'ROKT']
    prices = yf.download(space_tickers + ['SPY'], start = '2021-01-01')['Close']

    ##Company Financials
    financials = {}
    for t in ['RKLB', 'PL', 'IRDM', 'VSAT']:
        stock = yf.Ticker(t)
        financials[t] = {
            'revenue': stock.financials.loc['Total Revenue'].sort_index(),
            'gross_profit': stock.financials.loc['Gross Profit'].sort_index(),
            'fcf': stock.cashflow.loc['Free Cash Flow'].sort_index()
        }

    return{
        'fed_funds': fed_funds,
        'aerospace_ppi' : aerospace_ppi,
        'defense': defense,
        'prices': prices,
        'financials': financials
    }