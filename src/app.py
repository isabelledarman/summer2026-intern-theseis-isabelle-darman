from analysis import regimes, regression, returns as R, risk, robustness, scorecard as sc, profitability as prof, synthesis as syn, valuation
import streamlit as st
import datetime as dt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import config
from data.loaders import load_market_data

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
tab_intro, tab_reg, tab_regime, tab_risk, tab_valuation, tab_profitability, tab_synthesis, tab_verdict, tab_robust = st.tabs(
    ["Intro", "Regression", "Regimes", "Risk", "Valuation", "Profitability", "Synthesis", "Verdict", "Robustness"]
)

with tab_intro:
    st.header("The Question")
    st.markdown("**Launch costs have collapsed, satellite constellations are proliferating, and private capital is flooding into space infrastructure. This thesis evaluated "
                "whether the commercial space economy is a legitimate investable theme in the 2020s or a long-duration speculative bet with no near-term cash flows.**\n\n"
                "Have public space companies delivered shareholder returns backed by real business progress, or is the story still mostly narrative?")
    
    st.subheader("The Stance")
    st.markdown("**Real, but not yet derisked, and more narrative than earned.**\n"
                "Genuine businesses are emerging with a handful showing funamental driven returns and improving margins. "
                "However, across the pure-play universise, more of the sharpe-price gains have come from multiple re-rating rather than from"
                "operating progress, and the sector carries catastrophic drawdowns and heavy cash burn. "
                "Investable as a high-risk thematic bet for some names, but ont yet a derisked sector")
    
    st.subheader("How to Read This Dashboard")
    st.markdown("- **Valuation** - are prices justified by the business? P/S and a decomposition of returns into fundamentals vs. multiple re-rating. \n"
                "- **Profitability** - is the business progressing? Gross-margin trend, cash burn, and runway. \n" \
                "- **Synthesis** - the headline: per company, *earned* vs *narrative*. \n" \
                "- **Risk** - were investors paid for the risk? Sharpe, drawdown, beta. \n" \
                "- **Regression/Regimes** *(secondary)* - do fundamentals and interest rates relate to returns at all? Useful context, but macro is not the main sotry. \n"
                "- **Verdict** - the weighted, documented bottom line. \n"
                "- **Robustness** - how much to trust it (small-sample honesty)")
    
    st.subheader("Methodology and Choices")
    st.markdown(f"- **Universe:** {len(config.PURE_PLAY)} pure-play + {len(config.DIVERSIFIED)} diversified aerospace names. These companies are classified by whether space is the core business.\n"
                "- ** Returns:** annualized (CAGR) by default, so companies that listed at different dates are comparable and a common window is provided.\n"
                "- **Valuation:** price-to-sales (most names are pre-profit, so P/E is not usable). Market cap is computed as shares * price for a true time series. \n"
                "- **Return Decomposition:** price = P/S * sales-per-share, so return splits cleanly into fundamental (sales-per-sahre-growth) and re-reating (multiple change). \n"
                "- **Risk Weighted x2** in the verdict: catastrophic drawdowns disqualify regardless of upside.\n"
                "- **Caveats:** small sample (n = 16); annual revenue used as a TTM proxy; yFinance data quirks normalized where found. This is a weight of evidence read, not a statistical proof")
    
with tab_synthesis:
    st.header("Earned or Narrative?")
    st.caption("The thesis question, per company: did the return come from the business scaling (earned) or from investors paying a higher multiple (narrative)?"
               "Combines the return decomposition with operating progress (margins, cash).")
    
    ssum = syn.synthesis_summary(data, selected_tickers)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earned", ssum['earned'])
    c2.metric("Narrative", ssum['narrative'])
    c3.metric("Mixed", ssum['mixed'])
    c4.metric("Pure-plays", ssum['pure_play_total'])

    stab = syn.synthesis_table(data, selected_tickers)
    st.subheader("Share of return that was fundamental")
    st.caption("Higher - More of the move came from business scaling \n" \
    "Lower - More from multiple re-rating (narrative)")

    sp = stab.dropna(subset = ['fundamental_share']).sort_values("fundamental_share")
    if not sp.empty:
        vmap = {"Earned": "#3a9d52", "Mixed": "#e0a53f", "Narrative": "#e07a3f"}
        colors = [vmap.get(v, "#888888") for v in sp['verdict']]
        fig = go.Figure(go.Bar(x=sp["fundamental_share"], y=sp["ticker"],
                               orientation="h", marker_color=colors,
                               text=sp["verdict"], textposition="outside"))
        fig.update_layout(xaxis_title="Fundamental share of return (0-1)",
                          height=520, xaxis_range=[0, 1.15])
        st.plotly_chart(fig, width="stretch")

    st.subheader("Per-Company Read")
    st.dataframe(stab[['ticker', 'group', 'verdict', 'total_return_%', 'fundamental_%', 'rerating_%', 'margin_improving', 'fcf_positive', 'reason']], width = 'stretch', hide_index = True)


with tab_verdict:
    st.header(verdict['verdict'])
    c1, c2, c3 = st.columns(3)
    c1.metric("Net Weighted Score", f"{verdict['score']:+.0f}")
    c2.metric("Return Signals", f"{verdict['return_score']:+d}")
    c3.metric("Risk Signals", f"{verdict['risk_score']:+.0f}")

    ssum = syn.synthesis_summary(data, selected_tickers)
    earned, narrative, mixed = ssum['earned'], ssum['narrative'], ssum['pure_play_total']

    st.subheader('The Thesis')

    st.markdown(f"Across {ssum['pure_play_total']} pure-play space companies, **{ssum['earned']} show returns that were driven by fundamentals while"
                f"**{ssum['narrative']} were **narrative**, driven mainly by multiple re-reating, and {ssum['mixed']} are mixed."
                "On a risk basis, the sec remains punishing: pure-play drawdowns cluster far deeper than the mature aerospace names, and most are still burning cash. \n\n"
                "**Bottom Line:** the commercial space economy is *real but not yet derisked.* A minority of names have delivered shareholder returns backed"
                "by genuine business progress; for the majority, the market has paid up on expectation more than executio. It is investable today only as a high-risk, selective thematic bet.")
    
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
            xs = np.linspace(df['revenue_growth'].min() - 20, df['revenue_growth'].max() + 20, 100)
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
        fig.update_layout(xaxis_title = "Sharpe Ratio", height = 500)
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
        c3.metric("Share positive slope", f"{boot.share_positive_slope:.0%}")

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
             f"{top.get('note')}")
    
    st.subheader("Return-Convention Robustness")
    st.dataframe(robustness.convention_robustness(data, selected_tickers), width='stretch', hide_index = True)
    st.subheader("Regime-Data Sensitivity")
    st.caption("Does the regime story survive moving the cutoff dates?")
    st.dataframe(robustness.regime_data_sensitivity(data, selected_tickers), width='stretch', hide_index = True)

with tab_valuation:
    st.header("Is the price justified by the business?")
    st.caption("Market cap is computed as shares * price so P/S is real and time-varying. The decomposition splits each stock's move into business growth vs. multiple re-reating")
    cset1, cset2 = st.columns(2)

    target_ps = cset1.slider("'Normal' P/S to grow into", 1.0, 10.0, 4.0, 0.5)
    years = cset2.slider("Years to normalize", 1, 10, 5)
    vt = valuation.valuation_table(data, selected_tickers, target_ps=target_ps, years=years)
    
    st.subheader("Price-to-Sales Multiple")
    d = vt.dropna(subset=['ps_ratio']).sort_values('ps_ratio')
    if not d.empty:
        colors = ['#4682b4' if g == 'pure_play' else '#888888' for g in d['group']]
        fig = go.Figure(go.Bar(x=d['ps_ratio'], y = d['ticker'], orientation = 'h', marker_color = colors))
        fig.update_layout(xaxis_title = "P/S (market cap / revenue)", height = 460)
        st.plotly_chart(fig, width = 'stretch')

    st.subheader("Priced for perfection?")    
    st.caption("Top-left = expensive but slow growing (danger). Bottom-right = cheap to relative growth") 
    s = vt.dropna(subset=['ps_ratio', 'rev_growth_%'])

    if not s.empty:
        fig2 = go.Figure()
        for grp, color in [("pure_play", PURE_COLOR), ("diversified", DIV_COLOR)]:
            g = s[s["group"] == grp]
            fig2.add_trace(go.Scatter(x=g['rev_growth_%'], y=g['ps_ratio'], mode = "markers+text", text =g['ticker'], textposition="top center", name = grp, marker=dict(size = 13, color = color)))

        fig2.update_layout(xaxis_title = "Revenue Growth (%)", yaxis_title="P/S Multiple", height = 520)
        st.plotly_chart(fig2, width = 'stretch')

    st.subheader("What drove the returns: Business or the Multiple")
    st.caption("Fundamental = sales-per-share growth. Re-rating = change in P/S. Returns built mostly on re-reating are the speculation tell.")

    dec = valuation.decomposition_table(data, selected_tickers).dropna(subset=['fundamental_%', 'rerating_%'])    
    if not dec.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=dec['ticker'], y = dec['fundamental_%'], name = "Funamental (sales/share)", marker_color = "#3a9d52"))
        fig3.add_trace(go.Bar(x=dec['ticker'], y=dec['rerating_%'], name = "Multiple Re-Rating", marker_color="#e07a3f"))
        fig3.update_layout(barmode='relative', yaxis_title='Contribution to Return (%)', height = 480)
        st.plotly_chart(fig3, width = 'stretch')
        st.dataframe(dec[['ticker', 'group', 'total_return_%', 'fundamental_%', 'rerating_%']], width = 'stretch', hide_index = True)

    st.subheader('Valuation Table')
    st.dataframe(vt, width = 'stretch', hide_index = True)
    if vt['ev_to_rev'].isna().all():
        st.caption("EV/Revenue is blank")

with tab_profitability:
    st.header("Is the business actually progressing?")
    st.caption("Revenue growth isn't enough for this sector. Rising gross margins show the unit economics work; runway shows who survives long enough to deliver the story")

    summary = prof.profitability_summary(data, selected_tickers)
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Margins Improving", summary["margins_improving"])
    c2.metric("Margins Worsening", summary['margins_deteriorating'])    
    c3.metric("Cash-Positive", summary["cash_positive"])
    c4.metric("Burning Cash", summary["burning_cash"])

    pt = prof.profitability_table(data, selected_tickers)

    st.subheader("Gross Margin (Latest)")
    st.caption("Bar = Current Gross Margin, Green = Margin Improved, Red = Margin Deteriorating")


    m = pt.dropna(subset = ["gross_margin_%"]).sort_values("gross_margin_%")
    if not m.empty:
        colors = ["#3a9d52" if imp is True else "#e07a3f" for imp in m["margin_improving"]]
        fig = go.Figure(go.Bar(x=m["gross_margin_%"], y=m["ticker"],
                               orientation="h", marker_color=colors,
                               text=m["margin_change_pp"].map(
                                   lambda v: f"{v:+.0f}pp" if pd.notna(v) else ""),
                               textposition="outside"))
        fig.update_layout(xaxis_title="Gross margin (%)  \u2014  green improving / red worsening",
                          height=480)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Cash Runway (years until they must raise)")
    st.caption("cash on hand / annual burn. Blank = cash-generative or no cash data. Short runway and Heavy dilution = survival risk")

    rw = pt.dropna(subset=['runway_years']).sort_values("runway_years")
    if not rw.empty:
        colors = ["#4682b4" if g == "pure_play" else "#888888" for g in rw['group']]
        fig2 = go.Figure(go.Bar(x = rw["runway_years"], y = rw['ticker'], orientation = 'h', marker_color = colors))
        fig2.add_vline(x = 2, line_dash = "dash", line_color = "red", annotation_text = '2 yrs')
        fig2.update_layout(xaxis_title = "Runway (Years)", height = 420)
        st.plotly_chart(fig2, width = 'stretch')
    else:
        st.info("No runway data yet")

    st.subheader("Profitability Table")
    st.dataframe(pt, width = "stretch", hide_index = True)