import os
from helperfiles.data_loader import load_all_data
from helperfiles.regression import make_regression
from helperfiles.regime import make_regime
from helperfiles.visualize import make_initial_charts

def generate_report(regression_stats, regime_stats, fcf_poitive, fcf_negative, report_path):
    r2 = regression_stats['r_squared']
    p_reg = regression_stats['p_value']
    n_reg = regression_stats['n']

    t_stat = regime_stats['t_stat']
    p_regime = regime_stats['p_val']
    n_low = regime_stats['n_low']
    n_high = regime_stats['n_high']

    report = f"""# Space Economy: Early Stage or Pipe Dream?
## Investment Thesis Statistical Findings

**Thesis Question:** Is the commercial space economy a legitimeate investment theme in the 202s,
or a long-duration speculative bet with no near term cash flows?

**Sample:** {n_reg} companies spanning pure-play space and diversified aerospace/defense.

## 1. Does revenue growth predict stock returns? (Regression)

- Sample size: n = {n_reg}
- R Squared = {r2}
- p-value = {p_reg}

**Interpretation:** {"A statistically significant relationship exists between revenue growth and stock returns (p < 0.05)." if p_reg < 0.05 else "No statistically significant relationship was found between revenue growth and returns."}
Revenue growth explains only about {round(r2*100)}% of the variation in stock returns
across this sample. This means roughly {round((1-r2)*100)}% of return variation is driven by factors
other than current revenue growth.

## 2. Are returns sensitive to interest rate regimes? (Regime Analysis)

- Low-rate era sample: n = {n_low} companies
- High-rate era sample: n = {n_high} companies
- T-statistic = {t_stat}
- P-value = {p_regime}

**Interpretation:** {"There is a statistically significant difference in returns between hgih-rate and low rate eras (p < 0.05), supporting the view that space stocks behave as rate-sensitive, speculative assets." if p_reg < 0.05 else "No statistically significant difference in average returns between rate regimes was found at the sector-wide level. The charts show that the effect is concentrated in a few high-beta names rather than spread evenly."}


However, this aggregate reulst masks sharply divergen behavior by company type:

- **Diversified aerospace/defense** showed stable modest positive returns across nearly all regimes.
Consistent with a non-cyclical government revenue base acting as a buffer.
- **Pure-play space companies** showed extreme regime sensitiviy in *both* directions. RKLB, VSAT, and IRDM all
posted double-digit negative returns during the high-rate era, while ASTS gained +309% during the same period.
- In the rate-cutting era, pure play names dramatically outperformed, while diversified names were roughly flat

**Conclusion:** Regime/macro conditions matter less for individual stock selection in this sector than company-specific execution risk.
Pure-play space investing carries substantial idiosyncratic risk on top of any macro sensitivity.

## 3. Are companies generating real cash flow today?

- Companies currently Free Cash Flow Positive: {', '.join(fcf_poitive) if fcf_poitive else 'None'} ({len(fcf_poitive)} of {len(fcf_poitive) + len(fcf_negative)})
- Companies still cash-flow negative: {', '.join(fcf_negative) if fcf_negative else 'None'}

**Interpretation:** {"Only a minority of companies in the space economy currently generate positive free cash flow, directly supporting the 'no near-term cash flow' half of the thesis for most of the sector." if len(fcf_poitive) < len(fcf_negative) else "A majority of companies analyzed are FCF positive, weakening the 'no near-term cash flow' framing."}
Among pure-play space names specifically, IRDM stands out as the only consistently FCF-positive operator.

## Verdict

Based on the evidence above:

- Revenue growth and stock returns are weakly but significantly related
(R squared = {r2}, p = {p_reg}, n = {n_reg}). This means the fundamentals matter,
but explain less than a third of return variation.
- Interest rate regimes do not significanly affect *average* sectore returns
(p = {p_regime}), but pure-play space names show far greater idiosyncratic
volatility than diversified aerospace peers in every regime.
- {len(fcf_poitive)} of {len(fcf_poitive) + len(fcf_negative)} analyzed 
companies are currently free-cash-flow positive, with the only consistent perfomer
being a mature legacy operator (IRDM), not a new space company.


**Conclusion:** The commercial space economy is best characterized as 
**selectively investable with significant timing and selection risk.**
It is neither a fully legitimate broad-market theme yet nor a pure pipe dream.
Evidence supports real fundamental frivers in part of the sector (notably in mature operators),
while the majority of pure-play growth names remain speculative, cash-flow negative, and highly
sensitive to macro conditions.
"""
    
    with open(report_path, 'w') as f:
        f.write(report)

    print(report)
    return report

def compute_fcf(financials, tickers):
    positive = []
    negative = []

    for t in tickers:
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
    return positive, negative

def main():
    chart_dir = os.path.join(os.path.dirname(__file__), 'charts')
    os.makedirs(chart_dir, exist_ok=True)
    print("Running initial charts...\n")
    make_initial_charts()
    print("Running regression...\n")
    regression_stats = make_regression()
    print("Running regime analysis....\n")
    regime_stats = make_regime()
    print("All charts made successfully. Generating report.")

    data = load_all_data()
    tickers = ['RKLB', 'PL', 'IRDM', 'VSAT', 'ASTS', 'LMT', 'NOC', 'BA', 'RTX']
    fcf_positive, fcf_negative = compute_fcf(data['financials'], tickers)

    report_path = os.path.join(os.path.dirname(__file__), 'REPORT.md')
    generate_report(regression_stats, regime_stats, fcf_positive, fcf_negative, report_path)


if __name__ == '__main__':
    main()