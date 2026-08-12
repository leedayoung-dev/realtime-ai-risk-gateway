# Project B — Real-time Fraud & Suspicious Behavior Detection

중고거래 환경의 이상 행동을 분석해 Fraud Risk를 산출합니다.

PRD: [PRD-fraud-detection.md](./PRD-fraud-detection.md)

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | 이벤트 스키마 + 샘플 API | Done |
| M2 | Feature Store | Done |
| M3 | Supervised + Anomaly 모델 비교 | Done |
| M4 | Dashboard + Eval | Done |
| M5 | High-risk → Project C Insights push | Done |

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/train_fraud_models.py
PYTHONPATH=. uvicorn src.api.main:app --reload --port 8001
```

- Dashboard: http://localhost:8001/
- Docs: http://localhost:8001/docs

## API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/` | 대시보드 |
| GET | `/v1/users/{id}/risk` | Supervised risk |
| GET | `/v1/users/{id}/compare` | Supervised vs Anomaly |
| GET | `/v1/evaluation/compare` | 라벨 기반 비교 평가 |
