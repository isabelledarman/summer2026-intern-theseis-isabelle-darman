import pandas as pd
import config

def build_scorecard(reg, regime, risk_df, risk_weight: float = 2.0 , spy_ann: float = 13.0) -> list[dict]:
    signals = []
    pure = risk_df[risk_df["group"] == "pure_play"]

    def add(name, verdict, detail, weight, kind):
        signals.append({"name": name, "verdict": verdict, "detail": detail, "weight": weight, "kind": kind})
    
    med_sharpe = pure["sharpe"].median()
    if pd.isna(med_sharpe):
        add("Pure-play Sharpe", 0, "n/a", risk_weight, "risk")
    else:
        v = 1 if med_sharpe > 0.5 else (-1 if med_sharpe < 0 else 0)
        add("Pure-play Sharpe (median)", v, f"{med_sharpe:.2f}", risk_weight, "risk")

    med_dd = pure["max_drawdown_%"].median()
    if pd.isna(med_dd):
        add("Pure-play drawdown", 0, "n/a", risk_weight, "risk")
    else:
        v = 1 if med_dd > -60 else (-1 if med_dd < -80 else 0)
        add("Pure-play max drawdown (median)", v, f"{med_dd:.0f}%", risk_weight, "risk")

    if reg.slope is None:
        add("Revenue -> return link", 0, "n/a", 1, "return")
    else:
        v = 1 if reg.slope > 0 else -1
        flag = " (low power)" if reg.low_power else ""
        add("Revenue -> return link", v, f"slope = {reg.slope}, R\u00b2={reg.r_squared:.2f}{flag}", 1, "return")

    cut_col = config.REGIME_LABELS['cutting']
    if cut_col in regime.regime_df.columns and not regime.regime_df.empty:
        cut_med = regime.regime_df[cut_col].median()
        if pd.isna(cut_med):
            add("Return in cutting era", 0, "n/a", 1, "return")
        else:
            v = 1 if cut_med > 0 else -1
            add( "Return in cutting era", v, f"{cut_med:.0f}%", 1, "return")
    else:
        add("Regime resilience", 0, "n/a", 1, "return")

    pure_ret = pure["annual_return_%"].median()

    if pd.isna(pure_ret):
        add("Pure-play return vs SPY", 0, "n/a", 1, "return")
    else:
        v = 1 if pure_ret > spy_ann else (-1 if pure_ret < 0 else 0)   
        add("Pure-play return vs SPY", v, f"{pure_ret:.0f}% vs SPY ~{spy_ann:.0f}%", 1, "return")
 
    return signals

def compute_verdict(signals: list[dict]) -> dict:
    score = 0
    risk_score = 0
    return_score = 0
    for s in signals:
        contribution = s["verdict"] * s["weight"]
        score += contribution
        if s["kind"] == "risk":
            risk_score += contribution
        else:
            return_score += s["verdict"]

    n_decisive = sum(1 for s in signals if s["verdict"] != 0)
    if score >= 3:
        verdict = "The evidence LEANS TOWARD investable"
    elif score <= -3:
        verdict = "The evidence LEANS TOWARD pipe dream / premature"
    elif return_score > 0 and risk_score < 0:
        verdict = "Real, but too much risk"
    else:
        verdict = "The evidence is mixed"

    return{ "score": score, "risk_score": risk_score, "return_score": return_score, "n_decisive": n_decisive, "verdict": verdict }