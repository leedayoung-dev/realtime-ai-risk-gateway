# Project A — Real-time News Credibility Detection

뉴스 기사·출처·외부 증거·확산 패턴을 실시간 분석하여 **검증 필요도(Credibility Risk)** 를 산출합니다.  
Fake/Real 이진 분류가 목표가 아닙니다.

PRD: [PRD-news-credibility.md](./PRD-news-credibility.md)

## Pipeline

```text
News Collector → Kafka → Streaming
  → Claim Extraction → Evidence Retrieval
  → Feature Engineering → Feast/Redis
  → Risk Model → FastAPI → Dashboard
```

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | Collector + Kafka + Streaming 골격 | In progress |
| M2 | Claim Extraction + Evidence Retrieval | Planned |
| M3 | Feature Store + Risk Model | Planned |
| M4 | FastAPI + Dashboard + Early Detection 평가 | Planned |

## Layout

```text
project-a-news-credibility/
├── PRD-news-credibility.md
├── README.md
├── requirements.txt
├── docker-compose.yml
├── data/samples/
└── src/
    ├── collector/     # 뉴스 수집 → Kafka 발행
    ├── streaming/     # 실시간 처리 파이프라인
    ├── claims/        # Claim 추출
    ├── evidence/      # 증거 수집
    ├── features/      # Feature Engineering
    ├── risk/          # Credibility Risk 산출
    └── api/           # FastAPI 서빙
```

## Quick Start (M1)

```bash
# 인프라 (Kafka, Redis)
docker compose up -d

# 의존성
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 샘플 수집 → Kafka 발행 (로컬 스텁)
python -m src.collector.news_collector

# API (스켈레톤)
uvicorn src.api.main:app --reload --port 8000
```

## API (skeleton)

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/health` | 헬스체크 |
| GET | `/v1/articles/{article_id}/risk` | 기사 위험도 조회 |
| GET | `/v1/articles/{article_id}/claims` | Claim 목록 |
