import argparse
import sys
from pathlib import Path

from agent.analyze import allocate_budget, evaluate_snapshot
from agent.config import load_config
from agent.data import DataFetchError, fetch_snapshots
from agent.report import build_report, render_dashboard, save_report

BASE_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="미국 ETF(라쿠텐증권 성장투자枠 대상) 단기투자 상황 리포트 생성기"
    )
    parser.add_argument(
        "--session",
        choices=["morning", "lunch", "evening"],
        required=True,
        help="리포트를 생성할 시점 (아침/점심/저녁)",
    )
    parser.add_argument(
        "--config",
        default=str(BASE_DIR / "config.json"),
        help="config.json 경로 (기본값: 프로젝트 루트의 config.json)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="실제 API 호출 없이 가짜 데이터로 파이프라인을 테스트",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    try:
        snapshots = fetch_snapshots(config.watchlist, mock=args.mock)
    except DataFetchError as exc:
        print(f"[오류] {exc}", file=sys.stderr)
        sys.exit(1)

    evaluations = [
        evaluate_snapshot(snapshots[item.ticker], config.signal_thresholds)
        for item in config.watchlist
    ]
    evaluations = allocate_budget(evaluations, config.monthly_investment_jpy)

    report = build_report(
        session=args.session,
        monthly_investment_jpy=config.monthly_investment_jpy,
        currency=config.currency,
        snapshots=snapshots,
        evaluations=evaluations,
    )

    reports_dir = BASE_DIR / "reports"
    report_path = save_report(report, reports_dir)
    dashboard_path = render_dashboard(report, BASE_DIR / "dashboard.html")

    print(f"리포트 저장: {report_path}")
    print(f"대시보드 갱신: {dashboard_path}")
    print(f"요약: {report['summary']}")


if __name__ == "__main__":
    main()
