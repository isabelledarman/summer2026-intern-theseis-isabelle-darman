import pandas as pd
import numpy as mp
import matplotlib.pyplot as plt
from fredapi import Fred
import yfinance as yf
import os
from dotenv import load_dotenv
import time

load_dotenv()
fred = Fred(api_key = os.getenv('FRED_API_KEY'))

fed_funds = fred.get_series('FEDFUNDS', observation_start = '2010-01-01')
fed_funds_monthly = fed_funds.resample('M').last()
fed_funds_monthly.index = pd.DatetimeIndex(fed_funds_monthly.index.to_period('M').to_timestamp().values)

tickers = ['RKLB', 'PL', 'IRDM', 'VSAT']

prices = yf.download(tickers, start = "2021-01-01")['Close']
print(prices)
normalized = prices/prices.iloc[0] * 100
normalized_monthly = normalized.resample('M').last()
normalized_monthly.index = pd.DatetimeIndex(normalized_monthly.index.to_period('M').to_timestamp().values)