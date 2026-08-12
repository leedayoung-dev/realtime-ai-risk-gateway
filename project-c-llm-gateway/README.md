# Project C — LLM Gateway & AI Evaluation Platform

복수 LLM을 단일 Gateway로 통합하고, 요청 특성에 따라 모델을 라우팅합니다.  
**A/B 리스크 이벤트 → 요약(insight)** 과 **D 보안 게이트**를 연동합니다.

PRD: [PRD-llm-gateway.md](./PRD-llm-gateway.md)

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1–M4 | Gateway · Routing · Fallback · Eval | Done |
| M4+ | Project D Prompt Guard | Done |
| M5 | Agent Tools → D `/v1/agent/guard` | Done |
| M6 | A/B Risk Insights | Done |

## Flow

```text
A analyze / B compare  --push-->  C /v1/insights  → D guard → LLM summary
C /v1/insights/pull    --pull--->  A/B overview    → same

User → C /v1/chat | /v1/agent/run → D gates → route
```

## Quick Start

```bash
# A:8000  B:8001  D:8003  then C:
pip install -r requirements.txt
PYTHONPATH=. uvicorn src.api.main:app --reload --port 8002
```

Dashboard: http://localhost:8002/ → **Pull A/B Insights**

## API

| Method | Path | 설명 |
| --- | --- | --- |
| POST | `/v1/insights` | A/B push (high-risk event) |
| GET | `/v1/insights` | 최근 insight |
| POST | `/v1/insights/pull` | A/B overview에서 high-risk pull |
| POST | `/v1/chat` | 라우팅 + D 프롬프트 가드 |
| POST | `/v1/agent/run` | tool plan → D agent guard → stub |

## Routing Policy

| 요청 유형 | Primary → Fallback |
| --- | --- |
| simple | gemini → gpt |
| complex_reasoning | claude → gpt |
| long_context | gpt → claude |
