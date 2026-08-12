# Project D — AI Security Gateway & Monitoring

사용자와 LLM 사이에 AI Security Gateway를 두고, 통제된 환경에서 위협을 탐지·분류·차단합니다.  
공격 기법 배포가 아니라 **방어 유효성 검증**이 목적입니다.

PRD: [PRD-ai-security.md](./PRD-ai-security.md)

## Pipeline

```text
User / Agent
  → Prompt Guard (Rule / ML / Judge + DLP + Policy)
  → Agent Tool Guard (permission + arg risk)
  → ALLOW / REVIEW / BLOCK / MASK
  → Event Store + User Risk Profile
  → Defense Experiments
```

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | Gateway + Rule Detection | Done |
| M2 | DLP + Policy Engine | Done |
| M3 | ML / LLM Judge + 비교 실험 | Done (stub layers) |
| M4 | Monitoring + Risk Profiling | Done |
| M5 | Agent Security | Done |

## Agent Tool Policy

| Tool | Permission |
| --- | --- |
| search | allow |
| db_read | allow |
| db_write | block |
| file_read | allow |
| file_write | review |
| email | review |
| external_api | block |

추가로 인자에서 `DROP TABLE`, path traversal, DLP(PII/credential)가 보이면 정책을 강화합니다.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=. uvicorn src.api.main:app --reload --port 8003
```

브라우저: [http://127.0.0.1:8003/](http://127.0.0.1:8003/) · API Docs: `/docs`

## API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/` | Security Center 대시보드 |
| POST | `/v1/guard` | 입·출력 프롬프트 가드 |
| POST | `/v1/agent/guard` | Agent tool call 가드 |
| GET | `/v1/agent/policy` | Tool permission 테이블 |
| GET | `/v1/agent/samples` | 샘플 tool calls |
| POST | `/v1/agent/demo/seed` | Agent 데모 시드 |
| GET | `/v1/experiments/defense` | 방어 레이어 비교 |
| GET | `/v1/users/{id}/risk` | 사용자 risk profile |

## Integration (Project C)

LLM Gateway(`:8002`) 연동:

```text
C /v1/chat      → D /v1/guard (input/output)
C /v1/agent/run → D /v1/agent/guard (per tool) → stub execute → chat
```

C 설정: `SECURITY_GATEWAY_URL=http://127.0.0.1:8003` (기본값). D가 없으면 C는 fail-open.