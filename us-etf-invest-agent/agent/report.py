import json
from datetime import datetime, timezone
from pathlib import Path

from .analyze import Evaluation
from .data import MarketSnapshot

SIGNAL_LABELS = {
    "BUY_DIP": "매수 검토",
    "WATCH_OVERBOUGHT": "관망(과열)",
    "HOLD": "홀드",
}


def build_report(
    session: str,
    monthly_investment_jpy: float,
    currency: str,
    snapshots: dict[str, MarketSnapshot],
    evaluations: list[Evaluation],
) -> dict:
    holdings = []
    for e in evaluations:
        snap = snapshots[e.ticker]
        holdings.append(
            {
                "ticker": e.ticker,
                "name": e.name,
                "price": snap.price,
                "day_change_pct": snap.day_change_pct,
                "pct_from_sma25": e.pct_from_sma25,
                "pct_from_52w_high": snap.pct_from_52w_high,
                "market_state": snap.market_state,
                "signal": e.signal,
                "signal_label": SIGNAL_LABELS[e.signal],
                "reason": e.reason,
                "suggested_allocation": e.suggested_allocation_jpy,
            }
        )

    buy_signals = [h for h in holdings if h["signal"] == "BUY_DIP"]
    summary = (
        f"{len(buy_signals)}개 종목에서 조정 매수 신호 발생"
        if buy_signals
        else "특이 신호 없음 — 정기 적립 유지 권장"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session": session,
        "currency": currency,
        "monthly_investment_budget": monthly_investment_jpy,
        "summary": summary,
        "holdings": holdings,
    }


def save_report(report: dict, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = reports_dir / f"{date_str}_{report['session']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


_SESSION_LABELS = {"morning": "아침", "lunch": "점심", "evening": "저녁"}

_SIGNAL_COLORS = {
    "BUY_DIP": "#1f7a4d",
    "WATCH_OVERBOUGHT": "#a15c00",
    "HOLD": "#5b5750",
}


def render_dashboard(report: dict, output_path: Path) -> Path:
    session_label = _SESSION_LABELS.get(report["session"], report["session"])
    rows = "\n".join(
        f"""
        <tr>
          <td class="tkr">{h['ticker']}<span class="name">{h['name']}</span></td>
          <td>{h['price']:.2f}</td>
          <td class="{'pos' if h['day_change_pct'] >= 0 else 'neg'}">{h['day_change_pct']:+.2f}%</td>
          <td class="{'pos' if h['pct_from_sma25'] >= 0 else 'neg'}">{h['pct_from_sma25']:+.2f}%</td>
          <td><span class="badge" style="background:{_SIGNAL_COLORS[h['signal']]}">{h['signal_label']}</span></td>
          <td>{h['suggested_allocation']:,.0f}</td>
          <td class="reason">{h['reason']}</td>
        </tr>"""
        for h in report["holdings"]
    )

    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>단기투자 에이전트 리포트</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 2rem 1rem; background: #f7f5f2; color: #1a1714; }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #16140f; color: #ece7df; }} }}
  .wrap {{ max-width: 920px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
  .meta {{ color: #8a8378; font-size: 0.85rem; margin-bottom: 1.25rem; }}
  .summary {{ padding: 0.9rem 1.1rem; border-radius: 10px; background: rgba(122,92,56,0.1); margin-bottom: 1.5rem; font-size: 0.95rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ padding: 0.6rem 0.5rem; text-align: left; border-bottom: 1px solid rgba(0,0,0,0.08); vertical-align: top; }}
  @media (prefers-color-scheme: dark) {{ th, td {{ border-bottom-color: rgba(255,255,255,0.1); }} }}
  th {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: #8a8378; }}
  .tkr {{ font-weight: 600; display: flex; flex-direction: column; }}
  .name {{ font-weight: 400; font-size: 0.72rem; color: #8a8378; }}
  .pos {{ color: #1f7a4d; }}
  .neg {{ color: #b02a2a; }}
  .badge {{ color: #fff; padding: 0.2rem 0.55rem; border-radius: 999px; font-size: 0.72rem; white-space: nowrap; }}
  .reason {{ color: #6b6558; max-width: 260px; }}
  .wrap-scroll {{ overflow-x: auto; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>미국 ETF 단기투자 에이전트</h1>
  <div class="meta">세션: {session_label} · 생성 시각(UTC): {report['generated_at']} · 이번 세션 예산: {report['monthly_investment_budget']:,.0f} {report['currency']}</div>
  <div class="summary">{report['summary']}</div>
  <div class="wrap-scroll">
  <table>
    <thead>
      <tr><th>종목</th><th>현재가</th><th>당일 변동</th><th>25일선 대비</th><th>신호</th><th>제안 배분({report['currency']})</th><th>근거</th></tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
  </div>
</div>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
