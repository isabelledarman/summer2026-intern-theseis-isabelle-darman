import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from data_engine import load_all_data, get_regression_data, get_regime_data, ALL_TICKERS
import pandas as pd

st.set_page_config(page_title="Space Economy Thesis", layout= "wide")
st.title("Space Economy: Early Stage or Pipe Dream?")

#Cache the data loading so it only runs once
@st.cache_data
def get_cached_data():
    return load_all_data()

with st.spinner("Loading market data..."):
    data = get_cached_data()

st.success("Data loaded!")

st.sidebar.header("Controls")

st.sidebar.subheader("Pure-Play Space")
selected_pure_play = st.sidebar.multiselect(
    "Selected pure-play space companies",
    options=data['pure_play'],
    default = data['pure_play']
)

st.sidebar.subheader("Diversified Aerospace")
selected_diversified = st.sidebar.multiselect(
    "Selected diversified companies",
    options=data['diversified'],
    default=data['diversified']
)

selected_tickers = selected_pure_play + selected_diversified

if len(selected_tickers) < 2:
    st.warning("Select at least two companies to run the models.")
    st.stop()

result = get_regression_data(data, selected_tickers=selected_tickers)
df = result['df']

col1, col2, col3 = st.columns(3)
col1.metric("R Squared", f"{result['r_squared']:.3f}" if result['r_squared'] else "N/A")
col2.metric("P-Value", f"{result['p_value']:.3f}" if result['p_value'] else "N/A")
col3.metric("Sample size", result.get('n', 0))

#Build Charts

st.subheader("Does Revenue Growth Predict Stock Returns?")

fig, ax = plt.subplots(figsize=(10, 7))
group_colors = {'pure_play': 'steelblue', 'diversified': 'gray'}
    
for _, row in df.iterrows():
    ax.scatter(row['revenue_growth'], row['stock_return'], color=group_colors[row['group']], s = 150, zorder = 5)
    ax.annotate(row['ticker'], 
                xy=(row['revenue_growth'], row['stock_return']),
                xytext =(8, 4), textcoords='offset points',
                fontsize=12, fontweight='bold')

if result['slope'] is not None:
    x_line = np.linspace(df['revenue_growth'].min() - 20, df['revenue_growth'].max() + 20, 100)
    y_line = result['slope'] * x_line + result['intercept']
    ax.plot(x_line, y_line, color='black', linestyle='--', linewidth=1.5,
            label=f"Regression Line (R²={result['r_squared']:.2f})")

ax.axhline(y=0, color='gray', linestyle = ':', linewidth = 0.8)
ax.axvline(x = 0, color = 'gray', linestyle=':', linewidth = 0.8)

ax.set_xlabel('Revenue Growth (%) Since 2021', fontsize=13)
ax.set_ylabel('Stock Return (%) Since 2021', fontsize=13)

ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

st.pyplot(fig)
plt.close()

st.subheader("Underlying Data")
st.dataframe(df)

st.subheader("Does the federal funds rate affect returns?")

regime_result = get_regime_data(data, selected_tickers=selected_tickers)
df2 = regime_result['regime_df']
normalized = regime_result['normalized']

col1_r, col2_r = st.columns(2)
col1_r.metric("T-Statistic", f"{regime_result['t_stat']:.3f}" if regime_result['t_stat'] else "N/A")
col2_r.metric("P-Value", f"{regime_result['p_val']:.3f}" if regime_result['p_val'] else "N/A")

#plots

st.subheader("Returns Across Interest Rate Regimes")
fig, ax = plt.subplots(figsize = (14, 7))
x = np.arange(len(df2.index))
width = 0.25
colors = ['steelblue', 'coral', 'green']

for i, (col, color) in enumerate(zip(df2.columns, colors)):
    ax.bar(x + i * width, df2[col], width, label = col, color = color, alpha = 0.85)

ax.axhline(y = 0, color = 'black', linewidth = 0.8, linestyle = '--')
ax.set_xticks(x + width)
ax.set_xticklabels(df2.index, fontsize = 10)
ax.set_ylabel('Return (%)', fontsize = 12)
ax.set_title('Space Stock Returns Across Interest Rate Regimes', fontsize = 14, fontweight = 'bold')
ax.legend(fontsize=10)
ax.grid(True, alpha = 0.3, axis = 'y')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()

st.pyplot(fig)
plt.close(fig)

st.subheader("Space Sector vs S&P 500 Across Rate Regimes")

tickers_in_normalized = [t for t in selected_tickers if t in normalized.columns]
space_index = normalized[tickers_in_normalized].mean(axis = 1)
spy = normalized['SPY']

fig2, ax2 = plt.subplots(figsize=(12, 6))

ax2.axvspan(pd.Timestamp('2021-01-01'), pd.Timestamp('2022-03-01'),
        alpha=0.15, color='green', label='Low Rate Era')
ax2.axvspan(pd.Timestamp('2022-03-01'), pd.Timestamp('2024-09-01'),
        alpha=0.15, color='red', label='High Rate Era')
ax2.axvspan(pd.Timestamp('2024-09-01'), pd.Timestamp('2026-06-01'),
        alpha=0.15, color='blue', label='Rate Cutting Era')

ax2.plot(space_index.index, space_index.values,
        color='steelblue', linewidth=2, label='Space Sector (Equal Weighted)')
ax2.plot(spy.index, spy.values,
        color='black', linewidth=2, linestyle='--', label='S&P 500')

ax2.set_ylabel('Indexed Price (100 = Jan 2021)', fontsize=12)
ax2.set_title('Space Sector vs S&P 500 Across Rate Regimes', fontsize=14, fontweight='bold')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

st.pyplot(fig2)
plt.close(fig2)