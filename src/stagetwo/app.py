import streamlit as st
import datetime as dt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import config
from data.loaders import load_market_data
from analysis import (regression, regimes, risk, robustness, scorecard as sc, returns as R)

st.set_page_config(page_title="Space Economy Thesis", layout= "wide")

PURE_COLOR = "#4682b4"
DIV_COLOR = "#888888"
ACCENT = "#e07a3f"
st.title("Space Economy: Early Stage or Pipe Dream?")

#Cache the data loading so it only runs once
@st.cache_data(show_spinner="Loading market data...")
def get_data(force: bool = False):
    return load_market_data(force=force)

st.sidebar.title("Controls")

if st.sidebar.button("Refresh data (refetch)"):
    get_data.clear()
    data = get_data(force= True)
else:
    data = get_data()

st.sidebar.subheader("Universe")
selected_pure_play = st.sidebar.multiselect(
    "Selected pure-play space companies",
    config.PURE_PLAY,
    default = config.PURE_PLAY
)

st.sidebar.subheader("Diversified Aerospace")
selected_diversified = st.sidebar.multiselect(
    "Selected diversified companies",
    config.DIVERSIFIED,
    default=config.DIVERSIFIED
)

selected_tickers = selected_pure_play + selected_diversified

st.sidebar.subheader("Method")
method = st.sidebar.selectbox("Return Convention", ["annualized", "common"])
risk_weight = st.sidebar.slider("Risk-signal weight (verdict)", 1.0, 3.0, 2.0, 0.5, help = "How much risk signals count vs return signals")
rf = st.sidebar.number_input("Risk-free rate (annual, decimal)", value = float(config.DEFAULT_RISK_FREE), step = 0.005, format = "%.3f")
st.sidebar.subheader("Regime Cutoffs")
high_cut = st.sidebar.date_input("High-rate era start", value = dt.date(2022, 3, 1))
low_cut = st.sidebar.date_input("Cutting era starts", value=dt.date(2024, 9, 1))

config.REGIME_HIGH_CUTOFF = str(high_cut)
config.REGIME_LOW_CUTOFF = str(low_cut)

if len(selected_tickers) < 2:
    st.warning("Select at least two companies in the sidebar to run the models")
    st.stop()

##Compute everything
reg = regression.run_regression(data, selected_tickers, method=method)
regime = regimes.run_regime_analysis(data, selected_tickers)
risk_df = risk.risk_table(data.prices, selected_tickers, market = "SPY", rf=rf)
spy_ann = R.annualized_return(data.prices["SPY"]) if "SPY" in data.prices.columns else 13.0
spy_ann = spy_ann if spy_ann is not None else 13.0

signals = sc.build_scorecard(reg, regime, risk_df, risk_weight=risk_weight, spy_ann=spy_ann)
verdict = sc.compute_verdict(signals)

st.caption("Is the commercial space economy a legitimate invesatble theme or a long-duraction speculative bet?")
tab_verdict, tab_reg, tab_risk, tab_regime, tab_robust, tab_fund = st.tabs(
    ["Verdict", "Regression", "Risk", "Regimes", "Robustness", "Fundamentals"]
)

with tab_verdict:
    st.header(verdict['verdict'])
    c1, c2, c3 = st.columns(3)
    c1.metric("Net Weighted Score", f"{verdict['score']:+0f}")
    c2.metric("Return Signals", f"{verdict['return_score']:+d}")
    c3.metric("Risk Signals", f"{verdict['risk_score']:+0f}")

    st.subheader("Signals")
    rows = []
    for s in signals:
        mark = {1: "leans investable", 0: "inconclusive", -1: "leans pipe dream"}[s['verdict']]
        rows.append({"Signal": s['name'], "Read": mark, "Detail": s["detail"], "Weight": s['weight'], "Kind": s["kind"]})
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index = True)

with tab_reg:
    st.header("Does revenue growth predict returns?")
    c1, c2, c3 = st.columns(3)
    c1.metric("R\u00b2", f"{reg.r_squared:.3f}" if reg.r_squared is not None else "N/A")
    c2.metric("p-value", f"{reg.p_value:.3f}" if reg.p_value is not None else "N/A")
    c3.metric('n', reg.n)

    df = reg.df
    if not df.empty:
        fig = go.Figure()
        for grp, color in [("pure_play", PURE_COLOR), ("diversified", DIV_COLOR)]:
            g = df[df["group"] == grp]
            fig.add_trace(go.Scatter(
                x = g["revenue_growth"], y = g["stock_return"], mode = "markers+text", text = g["ticker"], textposition = "top center", name = grp, marker=dict(size = 14, color = color)))
        if reg.slope is not None:
            xs = np.linspace(df['revenue_growth'].min() - 20, df['revenue_growth'] + 20, 100)
            fig.add_trace(go.Scatter(x=xs, y= reg.slope*xs + reg.intercept, mode="lines", name=f"Fit (R\u00b2 = {reg.r_squared:.2f})",
                                         line = dict(color = "black", dash = "dash")))
        fig.update_layout(xaxis_title = "Revenue Growth (%)", yaxis_title = f"Stock Return (%, {method})", height = 560, hovermode = "closest")
        st.plotly_chart(fig, width='stretch')

        if reg.low_power:
            st.warning(f"n = {reg.n} is small, treat the p-value as suggestive.")
        
with tab_risk:
    st.header("Risk-Adjusted Returns")
    st.caption("Sharpe = retunr per unit of total volatility. Sortino penalizes only downside. Max drawdown = worst peak-to-trough loss.")
    d = risk_df.dropna(subset=["sharpe"]).sort_values("sharpe")
    if not d.empty:
        color = [PURE_COLOR if g == "pure_play" else DIV_COLOR for g in d["group"]]
        fig = go.Figure(go.Bar(x=d["sharpe"], y = d["ticker"], orientation = "h", marker_color = color))
        fig.add_vline(x=1, line_dash = "dash", line_color = "green", annotation_text="Sharpe = 1")
        fig.update_layout(xaxis_title = "Sharpe Ratio", height = 250)
        st.plotly_chart(fig, width = 'stretch')

    st.subheader("Full Risk Table")
    st.dataframe(risk_df, width='stretch', hide_index = True)

with tab_regime:
    st.header("Returns across interest-rate regimes")
    c1, c2 = st.columns(2)
    c1.metric("t-statistic", f"{regime.t_stat:.3f}" if regime.t_stat is not None else "N/A")
    c2.metric("p-value", f"{regime.p_value:.3f}" if regime.p_value is not None else "N/A")

    rdf = regime.regime_df
    if not rdf.empty:
        fig = go.Figure()
        palette = [PURE_COLOR, ACCENT, "#3a9d52"]
        for col, color in zip(rdf.columns, palette):
            fig.add_trace(go.Bar(x=rdf.index, y = rdf[col], name = col, marker_color = color))
        fig.update_layout(barmode = "group", yaxis_title = "Return (%)", height = 480)
        st.plotly_chart(fig, width = 'stretch')

    if regime.space_index is not None and regime.spy is not None:
        st.subheader("Space Sector vs S&P 500")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=regime.space_index.index, y=regime.space_index.values, name = "Space (equal weighted)", line = dict(color = PURE_COLOR)))
        fig2.add_trace(go.Scatter(x = regime.spy.index, y = regime.spy.values, name = "S&p 500", line = dict(color = "black", dash = "dash")))
        fig2.update_layout(yaxis_title = "Indexed (100 = Start)", height = 460)
        st.plotly_chart(fig2, width = "stretch")

    for n in regime.notes:
        st.caption(n)

with tab_robust:
    st.header("How much should you trust this?")
    st.subheader("Bootstrap (resampling the companies)")
    boot = robustness.bootstrap_regression(data, selected_tickers, method = method, n_boot = 5000)

    if boot.slope_ci is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Slope 95% CI low", f"{boot.slope_ci[0]:.3f}")
        c2.metric("Slope 95% CI high", f"{boot.slope_ci[1]:.3f}")
        c3.metric("Share positive slope", f"{boot.share_positive_slope:.05}")

        if boot.slope_crosses_zero:
            st.warning("The 95% CI for slope include 0. The potivie relationship is not robust.")
        else:
            st.success("The 95% CI for slope excludes 0, the direction is reasonably stable.")
    
    for n in boot.notes:
        st.caption(n)

    st.subheader("Leave-out influence (which names carry the results?)")
    jk = robustness.jackknife_regression(data, selected_tickers, method = method)
    if not jk.empty:
        st.dataframe(jk, width='stretch', hide_index = True)

    top = robustness.drop_top_performers(data, k = 2, selected_tickers=selected_tickers, method=method)
    st.write(f"**Drop top 2 ({top.get('dropped')}):** slope "
             f"{top.get('slope_full'):.3f} \u2192 {top.get('slope_without_top'):.3f}"
             "f{top.get('note')}")
    
    st.subheader("Return-Convention Robustness")
    st.dataframe(robustness.convention_robustness(data, selected_tickers), width='stretch', hide_index = True)
    st.subheader("Regime-Data Sensitivity")
    st.caption("Does the regime story survive moving the cutoff dates?")
    st.dataframe(robustness.regime_data_sensitivity(data, selected_tickers), width='stretch', hide_index = True)

