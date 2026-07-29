from dataclasses import dataclass

from .data import MarketSnapshot

BUY_DIP = "BUY_DIP"
WATCH_OVERBOUGHT = "WATCH_OVERBOUGHT"
HOLD = "HOLD"


@dataclass
class Evaluation:
    ticker: str
    name: str
    signal: str
    reason: str
    pct_from_sma25: float
    suggested_allocation_jpy: float = 0.0


def evaluate_snapshot(snap: MarketSnapshot, thresholds: dict) -> Evaluation:
    pct_from_sma25 = (snap.price - snap.sma25) / snap.sma25 * 100

    if (
        snap.day_change_pct <= thresholds["dip_buy_day_change_pct"]
        or pct_from_sma25 <= thresholds["dip_buy_below_sma25_pct"]
    ):
        reason = (
            f"당일 {snap.day_change_pct:+.2f}%, 25일 이평 대비 {pct_from_sma25:+.2f}% "
            "— 단기 조정폭이 커 분할매수 후보"
        )
        signal = BUY_DIP
    elif (
        snap.pct_from_52w_high >= thresholds["overbought_near_high_pct"]
        and snap.day_change_pct >= thresholds["overbought_day_change_pct"]
    ):
        reason = (
            f"52주 고점 대비 {snap.pct_from_52w_high:+.2f}%, 당일 {snap.day_change_pct:+.2f}% 급등 "
            "— 추가매수는 보류하고 관망"
        )
        signal = WATCH_OVERBOUGHT
    else:
        reason = f"당일 {snap.day_change_pct:+.2f}%, 특이 신호 없음 — 정기 적립 유지"
        signal = HOLD

    return Evaluation(
        ticker=snap.ticker,
        name=snap.name,
        signal=signal,
        reason=reason,
        pct_from_sma25=round(pct_from_sma25, 2),
    )


def allocate_budget(evaluations: list[Evaluation], monthly_investment_jpy: float) -> list[Evaluation]:
    """Suggest how to split this session's budget across the watchlist.

    If any ticker triggered BUY_DIP, the full budget is weighted toward the
    tickers with the deepest pullback. Otherwise the budget is split evenly
    across the whole watchlist as a standard dollar-cost-average.
    """
    dip_candidates = [e for e in evaluations if e.signal == BUY_DIP]

    if dip_candidates:
        weights = {}
        for e in dip_candidates:
            snap_drop = abs(min(e.pct_from_sma25, 0))
            weights[e.ticker] = max(snap_drop, 0.1)
        total_weight = sum(weights.values())
        for e in dip_candidates:
            e.suggested_allocation_jpy = round(
                monthly_investment_jpy * weights[e.ticker] / total_weight, 0
            )
    else:
        equal_share = round(monthly_investment_jpy / len(evaluations), 0)
        for e in evaluations:
            e.suggested_allocation_jpy = equal_share

    return evaluations
