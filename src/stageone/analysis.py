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

def generate_report():
    print("hi")

def main():
    chart_dir = os.path.join(os.path.dirname(__file__), 'charts')
    os.makedirs(chart_dir, exist_ok=True)
    print("Running initial charts...\n")
    make_initial_charts()
    print("Running regression...\n")
    regression_stats = make_regression()
    print("Running regime analysis....\n")
    regime_stats = make_regime()
    print("All charts made successfully. Running analysis.")
    verdict = compute_verdict(regression_stats, regime_stats)
    print(verdict)
    print("generating report....")


if __name__ == '__main__':
    main()