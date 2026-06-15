import os
from helperfiles.data_loader import load_all_data
from helperfiles.regression import make_regression
from helperfiles.regime import make_regime
from helperfiles.visualize import make_initial_charts

def compute_verdict(regression_results, regime_results):
    r_squared = regression_results['r_squared']
    p_val = regime_results['p_val']

    if r_squared > 0.4 and p_val < 0.05:
        verdict = 'legitimate investment'
    else:
        verdict = 'speculative bet'

    return verdict

def generate_report(regression_stats, regime_states, fcf_poitive, fcf_negative, report_path):
    r2 = regression_stats['r_squared']
    p_reg = regression_stats['p_value']
    t_stat = regime_states['t_stat']
    p_val = regime_states['p_val']

    report = f"""# Space Economy: Early Stage or Pipe Dream?
## Investment Thesis Statistical Findings

**Thesis Question:** Is the commercial space economy a legitimeate investment theme in the 202s,
or a long-duration speculative bet with no near term cash flows?


## 1. Does revenue growth predict stock returns? (Regression)

- R Squared = {r2}
- p-value = {p_reg}

**Interpretation:** {"A statistically significant relationship exists between revenue growth and stock returns (p < 0.05)." if p_reg < 0.05 else "No statistically significant relationship was found between revenue growth and returns."}
{"This means fundamentals partially explain returns. The sector is not purely narrative drive." if p_reg < 0.05 else "The suggests returns are driven more by sentiment than than current fundamentals."}
{"However, R squared of " + str(r2) + " means roughly " + str(round((1-r2) * 100)) + "% of return variation is explained by revenue growth. Narrative and macro conditions still play a large role." if r2 < 1 else ""}

## 2. Are returns sensitive to interest rate regimes? (Regime Analysis)

- T-statistic = {t_stat}
- P-value = {p_val}

**Interpretation:** {"There is a statistically significant difference in returns between hgih-rate and low rate eras (p < 0.05), supporting the view that space stocks behave as rate-sensitive, speculative assets." if p_reg < 0.05 else "No statistically significant difference in average returns between rate regimes was found at the sector-wide level. The charts show that the effect is concentrated in a few high-beta names rather than spread evenly."}

## 3. Are companies generating real cash flow today?

- Companies currently Free Cash Flow Positive: {', '.join(fcf_poitive) if fcf_poitive else 'None'} ({len(fcf_poitive)} of {len(fcf_poitive) + len(fcf_negative)})
- Companies still cash-flow negative: {', '.join(fcf_negative) if fcf_negative else 'None'}

**Interpretation:** {"Only a minority of companies in the space economy currently generate positive free cash flow, directly supporting the 'no near-term cash flow' half of the thesis for most of the sector." if len(fcf_poitive) < len(fcf_negative) else "A majority of companies analyzed are FCF positive, weakening the 'no near-term cash flow' framing."}

## Verdict

Based on the evidence above:

- Fundamentals (revenue growth) {"do" if p_reg < 0.05 else "do not"} have a statistically significant relationship with stock returns (R squared = {r2}, p = {p_reg}), but explain only part of the picture.
- The sector {"shows" if p_val < 0.05 else "does not show, at an aggregate level,"} statistically significant sensitivity to interest rate regimes, though individual high-growth names show sensitivity where the average does not.
- {len(fcf_poitive)} of {len(fcf_poitive) + len(fcf_negative)} analyszed companies are currently free-cash-flow positive.

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
        fcf = financials[t]['fcf'].dropna()
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