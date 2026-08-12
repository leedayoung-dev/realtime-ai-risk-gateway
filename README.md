# realtime-ai-risk-gateway

실시간 AI 기반 뉴스 신뢰도·사기 탐지, LLM 라우팅, AI Security Gateway

데이터 수집 → 실시간 처리 → 추론 → API 서빙 → 모니터링 → 평가까지 End-to-End로 다루는 AI 시스템 모노레포입니다.

## Projects

| 프로젝트 | 설명 | 문서 |
| --- | --- | --- |
| [project-a-news-credibility](./project-a-news-credibility) | 뉴스 신뢰도 위험도 실시간 산출 | [PRD](./project-a-news-credibility/PRD-news-credibility.md) |
| [project-b-fraud-detection](./project-b-fraud-detection) | 중고거래 사기·이상 행동 탐지 | [PRD](./project-b-fraud-detection/PRD-fraud-detection.md) |
| [project-c-llm-gateway](./project-c-llm-gateway) | LLM 라우팅·평가·비용 최적화 | [PRD](./project-c-llm-gateway/PRD-llm-gateway.md) |
| [project-d-ai-security](./project-d-ai-security) | AI Security Gateway·모니터링 | [PRD](./project-d-ai-security/PRD-ai-security.md) |

전체 로드맵: [초안.md](./초안.md)

## Architecture Overview

```text
DATA → REAL-TIME → AI
         │
    ┌────┼────┐
    ▼    ▼    ▼
 Predict Route Protect
  News    LLM   Security
  Fraud Gateway Gateway
    │     │      │
    └─────┼──────┘
          ▼
   SERVE → MONITOR → EVALUATE → IMPROVE
```

## Development Order

| Phase | 프로젝트 | 목표 |
| --- | --- | --- |
| 1 | News Credibility | AI + Streaming 기반 구축 |
| 2 | Fraud Detection | User Behavior + Anomaly Detection |
| 3 | LLM Gateway | Routing + Evaluation |
| 4–6 | AI Security | Gateway → Monitoring → Agent Security |

현재 진행: **pytest + GitHub Actions CI**

## Test / CI

```bash
# 각 프로젝트에서
cd project-d-ai-security && PYTHONPATH=. pytest -q
cd ../project-c-llm-gateway && SECURITY_ENABLED=false PYTHONPATH=. pytest -q
cd ../project-a-news-credibility && PYTHONPATH=. pytest -q
cd ../project-b-fraud-detection && PYTHONPATH=. pytest -q
```

GitHub Actions: `.github/workflows/ci.yml` (push/PR 시 A~D matrix로 pytest 실행)

## License

MIT
