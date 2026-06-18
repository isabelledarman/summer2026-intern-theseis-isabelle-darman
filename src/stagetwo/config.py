from datetime import date

PURE_PLAY: list[str] = ['RKLB', 'PL','IRDM', 'VSAT', 'ASTS', 'RDW', 'KTOS', 'SATL', 'LUNR']
DIVERSIFIED: list[str] = ['LMT', 'NOC', 'BA', 'RTX']
ALL_TICKERS: list[str] = PURE_PLAY + DIVERSIFIED
BENCHMARKS: list[str] = ['SPY', 'ARKX', 'ROKT']

START_DATE: str = '2021-01-01'
REGIME_HIGH_CUTOFF: str = '2022-03-01'
REGIME_LOW_CUTOFF: str = '2024-09-01'

REGIME_LABELS = {
    'low': 'Low Rate Era',
    'high': 'High Rate Era',
    'cutting': 'Rate Cutting Era'
}

DEFAULT_RISK_FREE: float = 0.04
TRADING_DAYS: int = 252

CACHE_DIR = 'data/cache'
CACHE_MAX_AGE_HOURS: float = 24.0

def classify(ticker: str) -> str:
    if ticker in PURE_PLAY:
        return 'pure_play'
    if ticker in DIVERSIFIED:
        return 'diversified'
    return 'benchmark'