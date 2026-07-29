# 미국 ETF 단기투자 에이전트

라쿠텐증권(楽天証券) 성장투자枠(成長投資枠)에서 매수 가능한 미국 ETF를 대상으로,
하루 아침/점심/저녁 세 번 실행해 시장 상황과 매수/홀드 액션을 제안해주는 로컬 스크립트입니다.

규칙 기반 휴리스틱 도구이며 투자 자문이 아닙니다. 최종 매수 판단과 금액은 본인 책임입니다.

## 설치

```bash
cd us-etf-invest-agent
pip install -r requirements.txt
```

## 설정 (`config.json`)

- `monthly_investment_jpy`: 이번 달 적립/추가매수 예산(엔화). 본인 금액으로 수정하세요.
- `watchlist`: 관심 ETF 목록(기본값은 라쿠텐증권 성장투자枠에서 흔히 거래되는 미국 ETF 예시입니다).
  **실제 매수 가능 여부는 라쿠텐증권 앱에서 최신 취급 종목을 반드시 재확인하세요.**
- `signal_thresholds`: 매수/관망 신호를 트리거하는 기준값. 필요에 맞게 조정 가능합니다.

## 실행

```bash
python main.py --session morning   # 아침
python main.py --session lunch     # 점심
python main.py --session evening   # 저녁
```

실행할 때마다:
- `reports/YYYY-MM-DD_<session>.json` 에 리포트가 저장됩니다.
- `dashboard.html` 이 최신 리포트 기준으로 갱신됩니다 (브라우저로 바로 열람 가능).

### 인터넷 없이 동작 확인 (mock 모드)

```bash
python main.py --session morning --mock
```

실시간 API 호출 대신 가짜 데이터로 파이프라인 전체(수집→분석→리포트→대시보드)를 테스트합니다.
이 저장소를 만든 샌드박스 환경은 조직 아웃바운드 정책상 금융 데이터 API 호출이 막혀 있어
이 옵션으로만 검증했습니다 — 실제 시세 조회는 일반 인터넷 환경(개인 PC, 서버 등)에서 정상 동작합니다.

## 신호 로직

각 ETF에 대해 다음 규칙으로 하나의 신호를 부여합니다.

| 신호 | 조건 | 의미 |
|---|---|---|
| `BUY_DIP` (매수 검토) | 당일 하락폭 또는 25일 이평선 대비 하락폭이 임계값 이하 | 분할매수 후보, 예산을 우선 배분 |
| `WATCH_OVERBOUGHT` (관망) | 52주 고점 근접 + 당일 급등 | 추가매수 보류 |
| `HOLD` (홀드) | 위 조건에 해당 없음 | 정기 적립 유지 |

예산 배분(`suggested_allocation`)은 `BUY_DIP` 종목이 있으면 하락폭이 큰 종목에 가중치를 두어
이번 세션 예산을 배분하고, 없으면 전체 관심종목에 균등 배분(표준 적립식)합니다.

## 하루 3번 자동 실행 (선택)

지금은 스크립트만 구축된 상태이며 자동화는 나중에 설정합니다. 예시 cron (서버/개인 PC 기준, KST):

```cron
0 8 * * *  cd /path/to/us-etf-invest-agent && python main.py --session morning
0 12 * * * cd /path/to/us-etf-invest-agent && python main.py --session lunch
0 21 * * * cd /path/to/us-etf-invest-agent && python main.py --session evening
```

## 프로젝트 구조

```
us-etf-invest-agent/
  config.json        # 투자 설정
  main.py             # CLI 진입점
  agent/
    config.py          # 설정 로더
    data.py             # 시세 수집 (yfinance / mock)
    analyze.py          # 신호 판정 + 예산 배분
    report.py           # JSON 리포트 + HTML 대시보드 생성
  reports/            # 세션별 JSON 리포트 저장 위치
  dashboard.html      # 최신 리포트 대시보드 (실행 시 갱신)
```
