import os
import json
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
import config

load_dotenv()

warnings.filterwarnings('ignore', category=FutureWarning)

#Result
@dataclass
class MarketData:
    prices: pd.DataFrame
    financials: dict[str, dict | None]
    macro: dict[str, pd.Series]
    loaded_at: datetime
    missing_prices: list[str] = field(default_factory=list)
    missing_financials: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def coverage_report(self) -> pd.DataFrame:
        rows = []
        for t in config.ALL_TICKERS:
            rows.append({
                "ticker": t,
                "group": config.classify(t),
                "has_prices": t in self.prices.columns and self.prices[t].notna().any(),
                "has_financials": self.financials.get(t) is not None,
            })
        return pd.DataFrame(rows)
    
def _cache_path(name: str) -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    return os.path.join(config.CACHE_DIR, name)

def _is_fresh(path: str) -> bool:
    if not os.path.exists(path):
        return False
    age_hours = (time.time() - os.path.getmtime(path))/3600.0
    return age_hours < config.CACHE_MAX_AGE_HOURS

def _load_prices(force: bool = False) -> tuple[pd.DataFrame, list[str], list[str]]:
    path = _cache_path("prices.parquet")
    notes: list[str] = []

    if not force and _is_fresh(path):
        prices = pd.read_parquet(path)
        notes.append(f"prices: loaded from cache ({path})")
    else:
        import yfinance as yf
        symbols = config.ALL_TICKERS + config.BENCHMARKS
        raw = yf.download(
            symbols, start = config.START_DATE,
            auto_adjust = True, progress = False
        )
        prices = raw['Close'] if 'Close' in raw.columns.get_level_values(0) else raw
        prices = prices.sort_index()
        if getattr(prices.index, "tz", None) is not None:
            prices.index = prices.index.tz_localize(None)
        prices.to_parquet(path)
        notes.append("prices: freshly fetched from yfinance")

    missing = [t for t in config.ALL_TICKERS if t not in prices.columns or prices[t].dropna().empty]

    return prices, missing, notes

def _clean_series(s: pd.Series) -> pd.Series:
    s = s.copy()
    s.index = pd.to_datetime(s.index)
    if getattr(s.index, "tz", None) is not None:
        s.index = s.index.tz_localize(None)
    s = s[~s.index.duplicated(keep = "last")].sort_index()
    return s

def _load_financials(force: bool = False) -> tuple[dict, list[str], list[str]]:
    #Fred
    path = _cache_path("financials.json")
    notes: list[str] = []

    if not force and _is_fresh(path):
        with open(path) as f:
            packed = json.load(f)
        financials = {t: _unpack(v) for t, v in packed.items()}
        missing = [t for t, v in financials.items() if v is None]
        notes.append('financials: loaded from cache')
        return financials, missing, notes

    import yfinance as yf
    financials: dict[str, dict | None] = {}
    missing: list[str] = []

    for t in config.ALL_TICKERS:
        try:
            stock = yf.Ticker(t)
            cf = stock.cashflow
            fin = stock.financials

            entry: dict[str, pd.Series] = {}
            if 'Total Revenue' in fin.index:
                entry['revenue'] = _clean_series(fin.loc['Total Revenue'])
            if "Gross Profit" in fin.index:
                entry['gross_profit'] = _clean_series(fin.loc['Gross Profit'])
            if "Free Cash Flow" in cf.index:
                entry['fcf'] = _clean_series(cf.loc['Free Cash Flow'])

            try:
                bs = stock.balance_sheet

                for key in ("Cash and Cash Equivalents", "Cash Cash Equivalents and Short Term Investments"):
                    if key in bs.index:
                        entry['cash'] = _clean_series(bs.loc[key])
                        break

                for key in ("Total Debt", "Long Term Debt", "Long Term Debt and Capital Lease Obligation"):
                    if key in bs.index:
                        entry['debt'] = _clean_series(bs.loc[key])
            except Exception:
                pass

            try:
                so = stock.get_shares_full(start=config.START_DATE)
                if so is not None and len(so):
                    entry['shares'] = _clean_series(so)
            except Exception:
                pass


            financials[t] = entry if 'revenue' in entry else None
            if financials[t] is None:
                missing.append(t)
        
        except Exception as e:
            financials[t] = None
            missing.append(t)
            notes.append(f"financials: {t} failed")
        time.sleep(0.3)

    with open(path, "w") as f:
        json.dump({t: _pack(v) for t, v in financials.items()}, f)
    notes.append("financials: freshly fetched")
    return financials, missing, notes

def _pack(entry: dict | None) -> dict | None:
    if entry is None:
        return None
    return {k: {str(i): (None if pd.isna(x) else float(x))
        for i, x in v.items()} for k, v in entry.items()}

def _unpack(packed: dict | None) -> dict | None:
    if packed is None:
        return None
    out = {}

    for k, v in packed.items():
        s = pd.Series(v)
        s.index = pd.to_datetime(s.index)
        out[k] = s.sort_index()
    return out

def _load_macro(force: bool = False) -> tuple[dict, list[str]]:
    path = _cache_path("macro.parquet")
    notes: list[str] = []
    series_ids = {
        'fed_funds': 'FEDFUNDS',
        'aerospace_ppo': 'PCU336411336411',
        'defense': 'FDEFX'
    }

    if not force and _is_fresh(path):
        df = pd.read_parquet(path)
        notes.append("macro: loaded from cache")
        return {c: df[c].dropna() for c in df.columns}, notes
    
    key = os.getenv('FRED_API_KEY')
    if not key:
        notes.append("macro: FRED_API_KEY not set - skipping macro series")
        return {}, notes
    
    from fredapi import Fred

    fred = Fred(api_key = key)
    macro = {}
    for name, sid in series_ids.items():
        try:
            macro[name] = fred.get_series(sid, observation_start= config.START_DATE)
        except Exception as e:
            notes.append(f"macro: {name} failed")

    if macro:
        pd.DataFrame(macro).to_parquet(path)
    return macro, notes

def load_market_data(force: bool = False) -> MarketData:
    prices, missing_p, notes_p = _load_prices(force)
    financials, missing_f, notes_f = _load_financials(force)
    macro, notes_m = _load_macro(force)

    return MarketData(
        prices = prices,
        financials = financials,
        macro = macro,
        loaded_at = datetime.now(timezone.utc),
        missing_prices = missing_p,
        missing_financials = missing_f,
        notes = notes_f + notes_m + notes_p

    )