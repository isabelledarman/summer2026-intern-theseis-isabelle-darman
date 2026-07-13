from analysis import regimes, regression, returns as R, risk, robustness, scorecard as sc, profitability as prof, synthesis as syn, valuation
import streamlit as st
import datetime as dt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import config
from data.loaders import load_market_data

st.set_page_config(page_title="Space Economy Thesis", layout= "wide")

PURE_COLOR = "#3b7dd8"
DIV_COLOR = "#94a3b8"
EARNED_COLOR = "#22c55e"
MIXED_COLOR = "#f59E0b"
NARR_COLOR = "#ef4444"
BG_CARD = "#f8fafc"
NEUTRAL = "#64748b"
BORDER = "#e2e8f0"

CHART_HEIGHT = 520
CHART_LAYOUT = dict(
    font = dict(family = "Inter, system0ui, sans-serif", size = 13, color = "#1e293b"),
    plot_bgcolor = "rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r = 20, t = 36, b = 10),
    hoverlabel=dict(font_size = 13, bgcolor = 'white'),
    xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#cbd5e1"),
    yaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#cbd5e1")
)

VERDICT_COLORS = {
    "Earned": EARNED_COLOR,
    "Mixed": MIXED_COLOR,
    "Narrative": NARR_COLOR,
    "insufficient data": NEUTRAL
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*='css']{ font-family: 'Inter', sustem-ui, sans-serif; }        
    .block-container{padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1200px}
            
    .thesis-header{
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        maring-bottom: 1.5rem
    }
            
    .thesis-header h1{
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
    }
            
    .thesis-header p {
        font-size: 0.95rem;
        color: #94a3b8;
        margin: 0
    }
            
    [data-testid="stMetric"]{
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0, 0,04);
    }
            
    [data-testid="stMetricLabel"]{
        font-size: 0.78rem;
        font-weight: 500;
        color: #64848b;
        text-transform: uppercase;
        letter-spacing: 0.04em
    }
    [data-testid="stMetricValuation"]{font-size: 1.4rem; font-weight: 700; color: #0f172a}
            
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.6rem 1.2rem;
        color: #64748B;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #3B7DD8;
        border-bottom-color: #3B7DD8;
    }
 
    /* Dataframes */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
 
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.9rem;
        color: #475569;
    }
 
    /* Verdict banner */
    .verdict-banner {
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 5px solid;
    }
    .verdict-banner h2 {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
    }
    .verdict-banner p {
        font-size: 0.9rem;
        margin: 0;
        opacity: 0.85;
    }
 
    /* Signal row styling */
    .signal-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .signal-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }
    .signal-icon { font-size: 1.3rem; flex-shrink: 0; margin-top: 1px; }
    .signal-name { font-weight: 600; font-size: 0.88rem; color: #0F172A; }
    .signal-detail { font-size: 0.8rem; color: #64748B; margin-top: 2px; }
    .signal-weight {
        font-size: 0.7rem;
        font-weight: 700;
        color: white;
        background: #3B7DD8;
        border-radius: 4px;
        padding: 1px 6px;
        margin-left: 6px;
    }
 
    /* Section dividers */
    .section-intro {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        font-size: 0.92rem;
        color: #334155;
        line-height: 1.6;
    }
 
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html = True)

st.markdown("""
            <div class = "thesis-header">
                <h1> Space Economy: Early Stage or Pipe Dream?</h1>
                <p>Is the commercial space economy a legitimate investable theme or a long duration speculative bet?</p>
            </div>
            """, unsafe_allow_html= True)

@st.cache_data(show_spinner="Loading market data...")
def get_data(force: bool = False):
    return load_market_data(force=force)

st.sidebar.title("Controls")

if st.sidebar.button("Refresh data"):
    get_data.clear()
    data = get_data(force= True)
else:
    data = get_data()

st.sidebar.subheader("Universe")
selected_pure_play = st.sidebar.multiselect(
    "Pure-Play Space Companies",
    config.PURE_PLAY,
    default = config.PURE_PLAY
)

selected_diversified = st.sidebar.multiselect(
    "Diversified Aerospace",
    config.DIVERSIFIED,
    default=config.DIVERSIFIED
)

selected_tickers = selected_pure_play + selected_diversified

st.sidebar.subheader("Method")
method = st.sidebar.selectbox("Return Convention", ["annualized", "common"])
risk_weight = st.sidebar.slider("Risk-Signal Weight", 1.0, 3.0, 2.0, 0.5, help = "How much risk signals count relative to return signals")
rf = st.sidebar.number_input("Risk-Free Rate (annual, decimal)", value = float(config.DEFAULT_RISK_FREE), step = 0.005, format = "%.3f")

st.sidebar.subheader("Regime Cutoffs")
high_cut = st.sidebar.date_input("High-Rate Era Start", value = dt.date(2022, 3, 1))
low_cut = st.sidebar.date_input("Cutting Era Start", value=dt.date(2024, 9, 1))
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
val_tab = valuation.valuation_table(data, selected_tickers)
prof_sum = prof.profitability_summary(data, selected_tickers)
syn_sum = syn.synthesis_summary(data, selected_tickers)

signals = sc.build_scorecard(reg, regime, risk_df, risk_weight=risk_weight, spy_ann=spy_ann, val_table=val_tab, prof_summary=prof_sum, syn_summary=syn_sum)
verdict = sc.compute_verdict(signals)

def build_dynamic_verdict(v: dict, signals: list, syn: dict, prof: dict, risk_df: pd.DataFrame) -> str:
    pure = risk_df[risk_df['group'] == 'pure_play']
    total = syn.get("pure_play_total", 0)
    earned = syn.get("earned", 0)
    narrative = syn.get("narrative", 0)
    mixed = syn.get("mixed", 0)
    margins_up = prof.get("margins_improving", 0)
    margins_down = prof.get("margins_deteriorating", 0)
    cash_pos = prof.get("cash_positive", 0)
    burning = prof.get("burning_cash", 0)
    med_dd = pure["max_drawdown_%"].median() if not pure.empty else None
    med_sharpe = pure['sharpe'].median() if not pure.empty else None

    parts = []

    if earned > narrative:
        parts.append(
            f"Across {total} pure-play space companies, the weight of evidence "
            f"tilts toward earned returns: **{earned}** companies show returns "
            f"driven primarily by business fundamentals, versus **{narrative}** "
            f"that are narrative-driven."
        )
    elif narrative > earned:
        parts.append(
            f"Across {total} pure-play space companies, the majority of returns "
            f"remain narrative-driven: **{narrative}** companies owe their gains "
            f"mainly to multiple re-rating, while only **{earned}** show returns "
            f"grounded in business fundamentals."
        )
    else:
        parts.append(
            f"Across {total} pure-play space companies, the picture is evenly "
            f"split: **{earned}** earned, **{narrative}** narrative, "
            f"**{mixed}** mixed."
        )
 
    # Profitability color
    if margins_up > margins_down:
        parts.append(
            f"On the operations side, there's genuine progress — "
            f"**{margins_up}** names are improving gross margins versus "
            f"**{margins_down}** deteriorating."
        )
    elif margins_down > margins_up:
        parts.append(
            f"Operating progress is weak: **{margins_down}** companies show "
            f"deteriorating margins versus only **{margins_up}** improving."
        )
 
    # Cash burn
    if burning > cash_pos:
        parts.append(
            f"Cash burn is the norm — **{burning}** are still burning through "
            f"reserves versus **{cash_pos}** that are cash-flow positive."
        )
    elif cash_pos > burning:
        parts.append(
            f"Cash generation is a bright spot: **{cash_pos}** names are "
            f"cash-flow positive, outnumbering the **{burning}** still burning."
        )
 
    # Risk color
    if med_dd is not None:
        if med_dd < -80:
            parts.append(
                f"Risk remains severe — the median pure-play peak-to-trough "
                f"drawdown is **{med_dd:.0f}%**, deep enough to wipe out "
                f"most position sizes."
            )
        elif med_dd < -60:
            parts.append(
                f"Risk is elevated: the median pure-play drawdown of "
                f"**{med_dd:.0f}%** is far deeper than typical equity drawdowns."
            )
        else:
            parts.append(
                f"Drawdown risk is moderate — the median pure-play max "
                f"drawdown of **{med_dd:.0f}%** is within range for "
                f"growth-stage companies."
            )
 
    # Bottom-line sentence based on the verdict category
    vtext = v["verdict"].lower()
    if "investable" in vtext:
        parts.append(
            "**Bottom line:** the evidence currently supports this as an "
            "investable theme — fundamentals are beginning to justify the prices "
            "for enough names to build a selective allocation."
        )
    elif "pipe dream" in vtext:
        parts.append(
            "**Bottom line:** at this stage, the sector looks more speculative "
            "than investable — returns are dominated by narrative, risk is "
            "uncompensated, and operating progress is too thin."
        )
    elif "derisked" in vtext:
        parts.append(
            "**Bottom line:** the commercial space economy is *real but not yet "
            "derisked.* Genuine businesses are emerging, but the risk profile is "
            "too severe to treat this as a broad sector bet. Investable only as a "
            "high-risk, selective thematic allocation."
        )
    else:
        parts.append(
            "**Bottom line:** the evidence is genuinely mixed. Neither bullish nor "
            "bearish signals dominate — the thesis depends on which names you pick "
            "and how much drawdown risk you can stomach."
        )
 
    return " ".join(parts)

tab_intro, tab_val, tab_prof, tab_syn, tab_risk, tab_verdict, tab_robust = st.tabs([
    "Intro", "Valuation", "Profitability", "Synthesis", "Risk", "Verdict", "Robustness"])

with tab_intro:
    st.header("The Question")
    st.markdown("""
                <div class='section-intro'>
                Launch costs have collapsed, satellite constellations are proliferating, and private capital is flooding into space infrastructure. This thesis evaluates 
                whether the commercial space economy is a legitimate investable theme in the 2020s or a long-duration speculative bet with no near-term cash flows.<br><br>

                <strong> Have public space companies delivered shareholder returns backed by real business progress, or is the story still mostly narrative?</strong>
                </div>""", unsafe_allow_html=True)
    
    st.subheader("The Stance")
    st.markdown("**Real, but not yet derisked, and more narrative than earned.**\n"
                "Genuine businesses are emerging with a handful showing funamental driven returns and improving margins. "
                "However, across the pure-play universise, more of the sharpe-price gains have come from multiple re-rating rather than from"
                "operating progress, and the sector carries catastrophic drawdowns and heavy cash burn. "
                "Investable as a high-risk thematic bet for some names, but ont yet a derisked sector")
    
    st.subheader("Dashboard Guide")
    
    st.markdown("- **Valuation** - are prices justified by the business? P/S and a decomposition of returns into fundamentals vs. multiple re-rating. \n"
                "- **Profitability** - is the business progressing? Gross-margin trend, cash burn, and runway. \n" \
                "- **Synthesis** - the headline: per company, *earned* vs *narrative*. \n" \
                "- **Risk** - were investors paid for the risk? Sharpe, drawdown, beta. \n" \
                "- **Verdict** - the weighted, documented bottom line. \n"
                "- **Robustness** - how much to trust it (small-sample honesty)")
    
    st.subheader("Methodology and Choices")
    st.markdown(f"- **Universe:** {len(config.PURE_PLAY)} pure-play + {len(config.DIVERSIFIED)} diversified aerospace names. These companies are classified by whether space is the core business.\n"
                "- **Returns:** annualized (CAGR) by default, so companies that listed at different dates are comparable and a common window is provided.\n"
                "- **Valuation:** price-to-sales (most names are pre-profit, so P/E is not usable). Market cap is computed as shares * price for a true time series. \n"
                "- **Return Decomposition:** price = P/S * sales-per-share, so return splits cleanly into fundamental (sales-per-sahre-growth) and re-reating (multiple change). \n"
                "- **Risk Weighted x2** in the verdict: catastrophic drawdowns disqualify regardless of upside.\n"
                "- **Caveats:** small sample (n = 16); annual revenue used as a TTM proxy; yFinance data quirks normalized where found. This is a weight of evidence read, not a statistical proof")
    
with tab_syn:
    st.header("Earned or Narrative?")
    st.markdown(""" <div class="section-intro">
    The thesis question, per company: did the return come from the business scaling (earned) or from investors paying a higher multiple (narrative)? 
    Combines the return decomposition with operating progress (margins, cash).</div>""", unsafe_allow_html = True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earned", syn_sum['earned'])
    c2.metric("Narrative", syn_sum['narrative'])
    c3.metric("Mixed", syn_sum['mixed'])
    c4.metric("Pure-plays", syn_sum['pure_play_total'])

    stab = syn.synthesis_table(data, selected_tickers)
    st.subheader("Share of Return That was Fundamental")
    st.caption("Higher → More of the move came from business scaling \n" \
    "Lower → More from multiple re-rating (narrative)")

    sp = stab.dropna(subset = ['fundamental_share']).sort_values("fundamental_share")
    if not sp.empty:
        colors = [VERDICT_COLORS.get(v, DIV_COLOR) for v in sp['verdict']]
        fig = go.Figure(go.Bar(
            x = sp['fundamental_share'], y = sp['ticker'], orientation ="h", marker_color = colors, text = sp['verdict'], textposition = 'outside'
        ))
        fig.update_layout(
            **CHART_LAYOUT,
            xaxis_title = "Fundamental Share of Return (0-1)",
            height = CHART_HEIGHT, xaxis_range = [0, 1.15]
        )
        st.plotly_chart(fig, width='stretch')

    st.subheader("Per-Company Read")
    st.dataframe(stab[['ticker', 'group', 'verdict', 'total_return_%', 'fundamental_%', 'rerating_%', 'margin_improving', 'fcf_positive', 'reason']], width='stretch', hide_index = True)


with tab_verdict:
    _vtext = verdict["verdict"]
    if "investable" in _vtext.lower():
        _vcolor, _vbg = EARNED_COLOR, "#F0FDF4"
    elif "pipe dream" in _vtext.lower():
        _vcolor, _vbg = NARR_COLOR, "#FEF2F2"
    elif "derisked" in _vtext.lower():
        _vcolor, _vbg = MIXED_COLOR, "#FFFBEB"
    else:
        _vcolor, _vbg = NEUTRAL, "#F8FAFC"

    

    score_pct = abs(verdict["score"]) / verdict["max_possible"] * 100 if verdict["max_possible"] else 0
 
    st.markdown(f"""
    <div class="verdict-banner" style="background:{_vbg}; border-left-color:{_vcolor};">
        <h2 style="color:{_vcolor};">{_vtext}</h2>
        <p>Net score: {verdict['score']:+.0f} out of ±{verdict['max_possible']:.0f}
        ({score_pct:.0f}% conviction) · {verdict['n_decisive']} of {len(signals)} signals decisive</p>
    </div>
    """, unsafe_allow_html=True)
 
    c1, c2, c3 = st.columns(3)
    c1.metric("Return Signals", f"{verdict['return_score']:+.0f}")
    c2.metric("Risk Signals", f"{verdict['risk_score']:+.0f}")
    c3.metric("Net Score", f"{verdict['score']:+.0f}")
 
    # ── Dynamic thesis paragraph ──
    st.subheader("The Thesis")
    dynamic_text = build_dynamic_verdict(verdict, signals, syn_sum, prof_sum, risk_df)
    st.markdown(dynamic_text)
 
    # ── Signal cards ──
    st.subheader("Scorecard (8 Signals)")
 
    # Build signal cards as HTML grid
    cards_html = '<div class="signal-grid">'
    for s in signals:
        icon = {1: "✅", 0: "➖", -1: "❌"}[s["verdict"]]
        weight_badge = (
            f'<span class="signal-weight">×{s["weight"]:.0f}</span>'
            if s["weight"] > 1 else ""
        )
        cards_html += f"""
        <div class="signal-card">
            <span class="signal-icon">{icon}</span>
            <div>
                <div class="signal-name">{s["name"]}{weight_badge}</div>
                <div class="signal-detail">{s["detail"]}</div>
            </div>
        </div>
        """
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)
 
    # ── Supporting context: regression + regime ──
    with st.expander("Supporting context: Regression & Regime analysis"):
        st.markdown("**Revenue growth → stock return regression**")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("R²", f"{reg.r_squared:.3f}" if reg.r_squared is not None else "N/A")
        rc2.metric("p-value", f"{reg.p_value:.3f}" if reg.p_value is not None else "N/A")
        rc3.metric("n", reg.n)
 
        df = reg.df
        if not df.empty:
            fig = go.Figure()
            for grp, color in [("pure_play", PURE_COLOR), ("diversified", DIV_COLOR)]:
                g = df[df["group"] == grp]
                fig.add_trace(go.Scatter(
                    x=g["revenue_growth"], y=g["stock_return"],
                    mode="markers+text", text=g["ticker"],
                    textposition="top center", name=grp.replace("_", " ").title(),
                    marker=dict(size=14, color=color, line=dict(width=1, color="white")),
                ))
            if reg.slope is not None:
                xs = np.linspace(
                    df["revenue_growth"].min() - 20,
                    df["revenue_growth"].max() + 20, 100,
                )
                fig.add_trace(go.Scatter(
                    x=xs, y=reg.slope * xs + reg.intercept,
                    mode="lines", name=f"Fit (R²={reg.r_squared:.2f})",
                    line=dict(color="#0F172A", dash="dash"),
                ))
            fig.update_layout(
                **CHART_LAYOUT,
                xaxis_title="Revenue Growth (%)",
                yaxis_title=f"Stock Return (%, {method})",
                height=480, hovermode="closest",
            )
            st.plotly_chart(fig, width='stretch')
            if reg.low_power:
                st.warning(f"n={reg.n} is small — treat the p-value as suggestive.")
 
        st.markdown("---")
        st.markdown("**Returns across interest-rate regimes**")
        rc1, rc2 = st.columns(2)
        rc1.metric("t-statistic", f"{regime.t_stat:.3f}" if regime.t_stat is not None else "N/A")
        rc2.metric("p-value", f"{regime.p_value:.3f}" if regime.p_value is not None else "N/A")
 
        rdf = regime.regime_df
        if not rdf.empty:
            fig = go.Figure()
            palette = [PURE_COLOR, NARR_COLOR, EARNED_COLOR]
            for col, color in zip(rdf.columns, palette):
                fig.add_trace(go.Bar(x=rdf.index, y=rdf[col], name=col, marker_color=color))
            fig.update_layout(
                **CHART_LAYOUT, barmode="group",
                yaxis_title="Return (%)", height=460,
            )
            st.plotly_chart(fig, width='stretch')
 
        if regime.space_index is not None and regime.spy is not None:
            st.markdown("**Space Sector vs S&P 500**")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=regime.space_index.index, y=regime.space_index.values,
                name="Space (equal-weighted)",
                line=dict(color=PURE_COLOR, width=2.5),
            ))
            fig2.add_trace(go.Scatter(
                x=regime.spy.index, y=regime.spy.values,
                name="S&P 500",
                line=dict(color="#0F172A", dash="dash", width=2),
            ))
            fig2.update_layout(
                **CHART_LAYOUT, yaxis_title="Indexed (100 = start)", height=440,
            )
            st.plotly_chart(fig2, width='stretch')
 
        for n in regime.notes:
            st.caption(n)

with tab_val:
    st.header("Is The Price Justified by the Bsiness?")
    st.caption("""<div class='section-intro'>Market cap is computed as shares x price so P/S is real and time-varying. The decomposition splits each stock's move into business growth vs. multiple re-reating.</div?""",
               unsafe_allow_html = True)
    
    cset1, cset2 = st.columns(2)

    target_ps = cset1.slider("'Normal' P/S to Grow Into", 1.0, 10.0, 4.0, 0.5)
    years = cset2.slider("Years to Mormalize", 1, 10, 5)
    vt = valuation.valuation_table(data, selected_tickers, target_ps=target_ps, years=years)
    
    st.subheader("Price-to-Sales Multiple")
    d = vt.dropna(subset=['ps_ratio']).sort_values('ps_ratio')
    if not d.empty:
        colors = [PURE_COLOR if g == 'pure_play' else DIV_COLOR for g in d['group']]
        fig = go.Figure(go.Bar(x=d['ps_ratio'], y = d['ticker'], orientation = 'h', marker_color = colors))
        fig.update_layout(**CHART_LAYOUT, xaxis_title = "P/S (market cap / revenue)", height = CHART_HEIGHT)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Priced for Perfection?")    
    st.caption("Top-left = expensive but slow growing (danger). Bottom-right = cheap to relative growth") 
    s = vt.dropna(subset=['ps_ratio', 'rev_growth_%'])

    if not s.empty:
        fig2 = go.Figure()
        for grp, color in [("pure_play", PURE_COLOR), ("diversified", DIV_COLOR)]:
            g = s[s["group"] == grp]
            fig2.add_trace(go.Scatter(x=g['rev_growth_%'], y=g['ps_ratio'], mode = "markers+text", text =g['ticker'], textposition="top center", name = grp, marker=dict(size = 14, color = color)))

        fig2.update_layout(**CHART_LAYOUT, xaxis_title = "Revenue Growth (%)", yaxis_title="P/S Multiple", height = CHART_HEIGHT)
        st.plotly_chart(fig2, width = 'stretch')

    st.subheader("What Drove the Returns: Business or the Multiple?")
    st.caption("Fundamental = sales-per-share growth. Re-rating = change in P/S. Returns built mostly on re-reating are the speculation tell.")

    dec = valuation.decomposition_table(data, selected_tickers).dropna(subset=['fundamental_%', 'rerating_%'])    
    if not dec.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=dec['ticker'], y = dec['fundamental_%'], name = "Funamental (sales/share)", marker_color = EARNED_COLOR))
        fig3.add_trace(go.Bar(x=dec['ticker'], y=dec['rerating_%'], name = "Multiple Re-Rating", marker_color=NARR_COLOR))
        fig3.update_layout(**CHART_LAYOUT, barmode='relative', yaxis_title='Contribution to Return (%)', height = CHART_HEIGHT)
        st.plotly_chart(fig3, width='stretch')
        st.dataframe(dec[['ticker', 'group', 'total_return_%', 'fundamental_%', 'rerating_%']], width='stretch', hide_index = True)

    st.subheader('Valuation Table')
    st.dataframe(vt, width='stretch', hide_index = True)
    if vt['ev_to_rev'].isna().all():
        st.caption("EV/Revenue is blank")

with tab_prof:
    st.header("Is the Business Actually Progressing?")
    st.caption("""<div class='section-intro'>Revenue growth isn't enough for this sector. Rising gross margins show the unit economics work; runway shows who survives long enough to deliver the story</div>""",
               unsafe_allow_html = True)

    summary = prof.profitability_summary(data, selected_tickers)
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Margins Improving", summary["margins_improving"])
    c2.metric("Margins Worsening", summary['margins_deteriorating'])    
    c3.metric("Cash-Positive", summary["cash_positive"])
    c4.metric("Burning Cash", summary["burning_cash"])

    pt = prof.profitability_table(data, selected_tickers)

    st.subheader("Gross Margin (Latest)")
    st.caption("Green = Margin Improved, Red = Margin Deteriorating")


    m = pt.dropna(subset = ["gross_margin_%"]).sort_values("gross_margin_%")
    if not m.empty:
        colors = [EARNED_COLOR if imp is True else NARR_COLOR for imp in m["margin_improving"]]
        fig = go.Figure(go.Bar(x=m["gross_margin_%"], y=m["ticker"],
                               orientation="h", marker_color=colors,
                               text=m["margin_change_pp"].map(
                                   lambda v: f"{v:+.0f}pp" if pd.notna(v) else ""),
                               textposition="outside"))
        fig.update_layout(**CHART_LAYOUT, xaxis_title="Gross margin (%)  -  green improving / red worsening",
                          height=CHART_HEIGHT)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Cash Runway (years until they must raise)")
    st.caption("Cash on hand / annual burn. Blank = cash-generative or no cash data. Short runway and heavy dilution = survival risk")

    rw = pt.dropna(subset=['runway_years']).sort_values("runway_years")
    if not rw.empty:
        colors = [PURE_COLOR if g == "pure_play" else DIV_COLOR for g in rw['group']]
        fig2 = go.Figure(go.Bar(x = rw["runway_years"], y = rw['ticker'], orientation = 'h', marker_color = colors))
        fig2.add_vline(x = 2, line_dash = "dash", line_color = NARR_COLOR, annotation_text = '2 yrs')
        fig2.update_layout(**CHART_LAYOUT, xaxis_title = "Runway (Years)", height = CHART_HEIGHT)
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("No runway data yet")

    st.subheader("Profitability Table")
    st.dataframe(pt, width='stretch', hide_index = True)

with tab_risk:
    st.header("Risk-Adjusted Returns")
    st.markdown("""<div class="section-intro">
    Sharpe = return per unit of total volatility. Sortino penalizes only downside.
    Max drawdown = worst peak-to-trough loss.
    </div>""", unsafe_allow_html=True)
 
    d = risk_df.dropna(subset=["sharpe"]).sort_values("sharpe")
    if not d.empty:
        color = [PURE_COLOR if g == "pure_play" else DIV_COLOR for g in d["group"]]
        fig = go.Figure(go.Bar(
            x=d["sharpe"], y=d["ticker"], orientation="h", marker_color=color,
        ))
        fig.add_vline(x=0, line_dash="solid", line_color="#CBD5E1")
        fig.add_vline(x=1, line_dash="dash", line_color=EARNED_COLOR,
                      annotation_text="Sharpe = 1", annotation_position="top")
        fig.update_layout(**CHART_LAYOUT, xaxis_title="Sharpe Ratio", height=CHART_HEIGHT)
        st.plotly_chart(fig, width='stretch')
 
    with st.expander("Full risk table"):
        st.dataframe(risk_df, width='stretch', hide_index=True)

with tab_robust:
    st.header("How much should you trust this?")
    st.markdown("""<div class="section-intro">
    With only ~16 companies, every statistical result comes with wide uncertainty.
    These checks quantify how fragile or stable the conclusions are.
    </div>""", unsafe_allow_html=True)
 
    st.subheader("Bootstrap (resampling the companies)")
    boot = robustness.bootstrap_regression(
        data, selected_tickers, method=method, n_boot=5000,
    )
    if boot.slope_ci is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Slope 95% CI low", f"{boot.slope_ci[0]:.3f}")
        c2.metric("Slope 95% CI high", f"{boot.slope_ci[1]:.3f}")
        c3.metric("Share positive slope", f"{boot.share_positive_slope:.0%}")
 
        if boot.slope_crosses_zero:
            st.warning("The 95% CI for slope includes 0 — the positive relationship is not robust.")
        else:
            st.success("The 95% CI for slope excludes 0 — the direction is reasonably stable.")
 
    for n in boot.notes:
        st.caption(n)
 
    st.subheader("Leave-out influence")
    st.caption("Which names carry the result? Dropping each one and re-fitting.")
    jk = robustness.jackknife_regression(data, selected_tickers, method=method)
    if not jk.empty:
        st.dataframe(jk, width='stretch', hide_index=True)
 
    top = robustness.drop_top_performers(
        data, k=2, selected_tickers=selected_tickers, method=method,
    )
    if isinstance(top.get("slope_full"), (int, float)):
        st.write(
            f"**Drop top 2 ({top.get('dropped')}):** slope "
            f"{top['slope_full']:.3f} → {top['slope_without_top']:.3f} — "
            f"{top['note']}"
        )
    else:
        st.write(top.get("note", ""))
 
    st.subheader("Return-Convention Robustness")
    st.dataframe(
        robustness.convention_robustness(data, selected_tickers),
        width='stretch', hide_index=True,
    )
 
    st.subheader("Regime-Date Sensitivity")
    st.caption("Does the regime story survive moving the cutoff dates?")
    st.dataframe(
        robustness.regime_data_sensitivity(data, selected_tickers),
        width='stretch', hide_index=True,
    )