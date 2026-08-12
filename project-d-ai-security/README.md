# Project D — AI Security Gateway & Monitoring

사용자와 LLM 사이에 AI Security Gateway를 두고, 통제된 환경에서 위협을 탐지·분류·차단합니다.  
공격 기법 배포가 아니라 **방어 유효성 검증**이 목적입니다.

PRD: [PRD-ai-security.md](./PRD-ai-security.md)

## Pipeline

```text
User → AI Application → Security Gateway
  → Prompt Security / DLP / Abuse Detection
  → Policy Engine (ALLOW / REVIEW / BLOCK)
  → LLM Router → Output Guard → User
```

## Milestones

| Phase | 산출물 | 상태 |
| --- | --- | --- |
| M1 | Gateway + Rule Detection | In progress |
| M2 | DLP + Policy Engine | Planned |
| M3 | ML / LLM Judge + 비교 실험 | Planned |
| M4 | Monitoring + Risk Profiling | Planned |
| M5 | Agent Security | Planned |

## Layout

```text
project-d-ai-security/
├── PRD-ai-security.md
├── README.md
├── requirements.txt
├── data/samples/
└── src/
    ├── detection/     # Rule / ML stub / LLM Judge stub
    ├── dlp/           # PII / Credential 탐지·마스킹
    ├── policy/        # ALLOW / REVIEW / BLOCK
    ├── gateway/       # 요청 선처리 + Output Guard
    └── api/           # FastAPI
```

## Quick Start (M1)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=. uvicorn src.api.main:app --reload --port 8003
```

## API (skeleton)

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/health` | 헬스체크 |
| POST | `/v1/inspect` | 입력 보안 검사 |
| POST | `/v1/guard` | 입·출력 가드 + 정책 결정 |
| GET | `/v1/samples` | 테스트셋 목록 |
