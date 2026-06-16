from fredapi import Fred
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
import time
from scipy import stats 

load_dotenv()

PURE_PLAY = ['RKLB', 'PL', 'IRDM', 'VSAT', 'ASTS', 'RDW', 'KTOS', 'SATL', 'LUNR']
DIVERSIFIED = ['LMT', 'NOC', 'BA', 'RTX']
ALL_TICKERS = PURE_PLAY + DIVERSIFIED

def load_all_data():
    #Fred
    fred = Fred(api_key = os.getenv('FRED_API_KEY'))
    fed_funds = fred.get_series('FEDFUNDS', observation_start = '2021-01-01')
    aerospace_ppi = fred.get_series('PCU336411336411', observation_start = '2021-01-01')
    defense = fred.get_series('FDEFX', observation_start = '2021-01-01')

    prices = yf.download(ALL_TICKERS + ['SPY', 'ARKX', 'ROKT'], start = '2021-01-01')['Close']
    financials = {}

    for t in ALL_TICKERS:
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
        'pure_play': PURE_PLAY,
        'diversified': DIVERSIFIED
    }

def get_regression_data(data, selected_tickers = None):
    financials = data['financials']
    prices = data['prices']
    pure_play = data['pure_play']

    all_tickers = data['pure_play'] + data['diversified']

    if selected_tickers is None:
        selected_tickers = all_tickers

    tickers = [t for t in selected_tickers if financials.get(t) is not None]

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

    if len(df) < 2:
        return {'df': df, 'r_squared': None, 'p_value': None, 'slope': None, 'intercept': None}

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['revenue_growth'],
        df['stock_return']
    )

    return{
        'df': df,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'slope': slope,
        'intercept': intercept,
        'n': len(df)
    }

def get_regime_data(data, low_high_cutoff = '2022-03-01', high_cut_cutoff = '2024-09-01', selected_tickers = None):
    prices = data['prices']
    pure_play = data['pure_play']
    diversified = data['diversified']

    normalized = prices / prices.iloc[0] * 100

    all_tickers = pure_play + diversified
    if selected_tickers is None:
        selected_tickers = all_tickers

    space_tickers = [t for t in selected_tickers if t in normalized.columns]

    low_rate   = normalized[normalized.index < low_high_cutoff]
    high_rate  = normalized[(normalized.index >= low_high_cutoff) & (normalized.index < high_cut_cutoff)]
    cutting    = normalized[(normalized.index >= high_cut_cutoff)]

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
    }).dropna(thresh=2)

    #T-Test: are returns different across regimes?
    low_vals = list(low_returns.values())
    high_vals = list(high_returns.values())

    if len(low_vals) >= 2 and len(high_vals) >= 2:
        t_stat, p_val = stats.ttest_ind(low_vals, high_vals)
    else:
        t_stat, p_val = None, None

    pure_play_in_prices = [t for t in pure_play if t in normalized.columns and t in selected_tickers]
    space_index = normalized[pure_play_in_prices].mean(axis = 1) if pure_play_in_prices else None
    spy = normalized['SPY']

    return{
        'regime_df': regime_df,
        't_stat': t_stat,
        'p_val': p_val,
        'normalized': normalized,
        'space_index': space_index,
        'spy': spy,
        'low_high_cutoff': low_high_cutoff,
        'high_cut_off': high_cut_cutoff
    }

def initial_charts(data, selected_tickers = None):
    print("hit")


def get_fcf_status(data, selected_tickers=None):
    financials = data['financials']
    all_tickers = data['pure_play']+data['diversified']

    if selected_tickers is None:
        selected_tickers = all_tickers

    positive = []
    negative = []

    for t in selected_tickers:
        if financials[t] is None:
            continue
        fcf = financials[t]['fcf'].dropna()
        if len(fcf) == 0:
            continue
        latest = fcf.sort_index().iloc[-1]
        if latest > 0:
            positive.append(t)
        else:
            negative.append(t)
    return {'positive': positive, 'negative': negative}