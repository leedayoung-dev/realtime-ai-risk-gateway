# Project C — LLM Gateway & AI Evaluation Platform

복수 LLM을 단일 Gateway로 통합하고, 요청 특성에 따라 모델을 라우팅합니다.  
Quality / Latency / Cost / Availability를 측정해 사용 전략을 수립합니다.

PRD: [PRD-llm-gateway.md](./PRD-llm-gateway.md)

## Pipeline

```text
Application → AI Gateway → Request Analyzer → Routing Engine
  → GPT / Claude / Gemini → Evaluation → Analytics
```

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | Gateway + Provider Adapter(stub) | In progress |
| M2 | Request Analyzer + Routing Engine | Planned |
| M3 | Fallback | Planned |
| M4 | Evaluation + Analytics | Planned |

## Layout

```text
project-c-llm-gateway/
├── PRD-llm-gateway.md
├── README.md
├── requirements.txt
├── data/samples/
└── src/
    ├── analyzer/      # 요청 유형 분류
    ├── routing/       # 모델 라우팅 + Fallback
    ├── providers/     # LLM Provider stubs
    ├── evaluation/    # Quality / Latency / Cost
    └── api/           # FastAPI Gateway
```

## Quick Start (M1)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=. uvicorn src.api.main:app --reload --port 8002
```

## API (skeleton)

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/health` | 헬스체크 |
| POST | `/v1/chat` | 라우팅 + (stub) 응답 |
| POST | `/v1/evaluate` | 동일 질의 모델 비교 |
| GET | `/v1/analytics/summary` | 평가 요약 |
