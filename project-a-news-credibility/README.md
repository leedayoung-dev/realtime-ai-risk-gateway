# Project A — Real-time News Credibility Detection

뉴스 기사·출처·외부 증거·확산 패턴을 실시간 분석하여 **검증 필요도(Credibility Risk)** 를 산출합니다.

PRD: [PRD-news-credibility.md](./PRD-news-credibility.md)

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | Collector + Kafka + Streaming 골격 | Done |
| M2 | Claim Extraction + Evidence Retrieval | Done |
| M3 | Feature Store + Risk Model | Done |
| M4 | Dashboard + Early Detection 평가 | Done |
| M4+ | RSS/Fixture Collect → Bus → Analyze | Done |
| M5 | High-risk → Project C Insights push | Done |

## Quick Start

```bash
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/train_risk_model.py
PYTHONPATH=. uvicorn src.api.main:app --reload --port 8000
```

- Dashboard: http://localhost:8000/
- API Docs: http://localhost:8000/docs

## Realtime path (Kafka optional)

```text
RSS/Fixture → Collector → Bus(Kafka|memory) → Streaming analyze → Registry/API/Dashboard
```

Kafka/Redis가 없어도 in-memory bus/feature store로 동일 흐름이 동작합니다.

```bash
# fixture 수집 + 파이프라인
curl -X POST http://127.0.0.1:8000/v1/collect/rss \
  -H 'Content-Type: application/json' \
  -d '{"use_fixture": true, "run_pipeline": true}'
```

## Evaluate

```bash
PYTHONPATH=. python scripts/eval_early_detection.py 50
```
