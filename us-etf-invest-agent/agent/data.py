import random
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class MarketSnapshot:
    ticker: str
    name: str
    price: float
    previous_close: float
    day_change_pct: float
    sma5: float
    sma25: float
    week52_high: float
    pct_from_52w_high: float
    market_state: str
    as_of: str


class DataFetchError(RuntimeError):
    """Raised when live market data cannot be retrieved."""


def fetch_snapshots(watchlist, mock: bool = False) -> dict[str, MarketSnapshot]:
    """Fetch a market snapshot for every ticker in watchlist.

    watchlist: list of objects with .ticker and .name (see agent.config.WatchlistItem)
    mock: when True, generates deterministic fake data instead of calling yfinance.
    """
    if mock:
        return {item.ticker: _mock_snapshot(item.ticker, item.name) for item in watchlist}
    return {item.ticker: _fetch_live_snapshot(item.ticker, item.name) for item in watchlist}


def _mock_snapshot(ticker: str, name: str) -> MarketSnapshot:
    rng = random.Random(ticker)
    base_price = rng.uniform(50, 450)
    day_change_pct = rng.uniform(-4.5, 4.5)
    previous_close = base_price / (1 + day_change_pct / 100)
    sma5 = base_price * rng.uniform(0.97, 1.03)
    sma25 = base_price * rng.uniform(0.93, 1.07)
    week52_high = base_price * rng.uniform(1.0, 1.25)
    pct_from_high = (base_price - week52_high) / week52_high * 100
    return MarketSnapshot(
        ticker=ticker,
        name=name,
        price=round(base_price, 2),
        previous_close=round(previous_close, 2),
        day_change_pct=round(day_change_pct, 2),
        sma5=round(sma5, 2),
        sma25=round(sma25, 2),
        week52_high=round(week52_high, 2),
        pct_from_52w_high=round(pct_from_high, 2),
        market_state="MOCK",
        as_of=datetime.now(timezone.utc).isoformat(),
    )


def _fetch_live_snapshot(ticker: str, name: str) -> MarketSnapshot:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise DataFetchError(
            "yfinance가 설치되어 있지 않습니다. `pip install -r requirements.txt` 를 실행하세요."
        ) from exc

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="60d", interval="1d")
        if hist.empty:
            raise DataFetchError(f"{ticker}: 시세 데이터를 가져오지 못했습니다.")

        fast_info = t.fast_info
        price = float(fast_info.get("lastPrice") or hist["Close"].iloc[-1])
        previous_close = float(fast_info.get("previousClose") or hist["Close"].iloc[-2])
        day_change_pct = (price - previous_close) / previous_close * 100

        closes = hist["Close"]
        sma5 = float(closes.tail(5).mean())
        sma25 = float(closes.tail(25).mean())
        week52_high = float(fast_info.get("yearHigh") or closes.max())
        pct_from_high = (price - week52_high) / week52_high * 100

        market_state = fast_info.get("marketState", "UNKNOWN")

        return MarketSnapshot(
            ticker=ticker,
            name=name,
            price=round(price, 2),
            previous_close=round(previous_close, 2),
            day_change_pct=round(day_change_pct, 2),
            sma5=round(sma5, 2),
            sma25=round(sma25, 2),
            week52_high=round(week52_high, 2),
            pct_from_52w_high=round(pct_from_high, 2),
            market_state=str(market_state),
            as_of=datetime.now(timezone.utc).isoformat(),
        )
    except DataFetchError:
        raise
    except Exception as exc:
        raise DataFetchError(
            f"{ticker} 시세 조회 실패: {exc}. 인터넷 연결 및 티커 심볼을 확인하세요."
        ) from exc
