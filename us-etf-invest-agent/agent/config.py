import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WatchlistItem:
    ticker: str
    name: str


@dataclass
class Config:
    monthly_investment_jpy: float
    currency: str
    watchlist: list[WatchlistItem]
    signal_thresholds: dict
    sessions: list[str]

    @property
    def tickers(self) -> list[str]:
        return [item.ticker for item in self.watchlist]


def load_config(path: str | Path) -> Config:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    return Config(
        monthly_investment_jpy=raw["monthly_investment_jpy"],
        currency=raw.get("currency", "JPY"),
        watchlist=[WatchlistItem(**item) for item in raw["watchlist"]],
        signal_thresholds=raw["signal_thresholds"],
        sessions=raw["sessions"],
    )
