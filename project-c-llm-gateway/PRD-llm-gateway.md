# PRD — LLM Gateway & AI Evaluation Platform

| 항목 | 내용 |
| --- | --- |
| 프로젝트 코드 | Project C |
| 문서 버전 | 1.0 |
| 상태 | Draft |
| 연관 문서 | `../초안.md` |

---

## 1. 개요

복수 LLM을 단일 Gateway로 통합하고, 요청 특성에 따라 모델을 라우팅한다. Quality, Latency, Cost, Availability를 측정하여 LLM 사용 전략을 수립하는 플랫폼이다.

## 2. 문제 정의

| 구분 | 내용 |
| --- | --- |
| 문제 | 애플리케이션이 개별 LLM API에 직접 의존하면 비용·지연·가용성 최적화가 어렵다. |
| 영향 | 과도한 비용, 장애 시 중단, 모델별 품질 편차 관리 불가 |
| 기회 | Gateway 기반 라우팅·Fallback·평가로 운영 효율을 높일 수 있다. |

## 3. 목표 및 비목표

### 목표

- 요청 분석 기반 Model Routing 구현
- Primary 실패 시 Fallback 경로 제공
- 모델별 Quality / Latency / Cost 비교 평가 및 Analytics

### 비목표

- 자체 Foundation Model 학습
- 모든 LLM Provider 지원
- Project D 수준의 보안 Gateway 완전 구현(연계만 고려)

## 4. 사용자 및 이해관계자

| 역할 | 니즈 |
| --- | --- |
| 애플리케이션 개발자 | 단일 API로 다중 모델 사용 |
| AI Platform 담당자 | 라우팅 정책·비용·지연 관리 |
| 평가 담당자 | 모델 품질 비교 및 전략 수립 |

## 5. 기능 요구사항

### 5.1 Gateway 및 라우팅

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| C-F-01 | Application 요청을 AI Gateway로 수신한다. | P0 |
| C-F-02 | Request Analyzer가 요청 유형을 분류한다. | P0 |
| C-F-03 | Routing Engine이 모델로 라우팅한다. | P0 |

| 요청 유형 | 라우팅 |
| --- | --- |
| Simple Request | Fast / Cheap Model |
| Complex Reasoning | High-performance Model |
| Long Context | Long-context Model |

### 5.2 Fallback

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| C-F-04 | Primary Model Timeout/Failure 시 Fallback Model로 전환한다. | P0 |
| C-F-05 | Fallback 발생 이벤트와 원인을 기록한다. | P1 |

```text
Primary Model → Timeout → Fallback Model → Response
```

### 5.3 Evaluation 및 Analytics

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| C-F-06 | 동일 질의에 대해 복수 모델 결과를 비교한다. | P0 |
| C-F-07 | Quality, Latency, Cost, Availability를 측정한다. | P0 |
| C-F-08 | Analytics 대시보드 또는 리포트를 제공한다. | P1 |

## 6. 비기능 요구사항

| ID | 항목 | 기준 |
| --- | --- | --- |
| C-NF-01 | Availability | Provider 장애 시 Fallback으로 서비스 연속성 유지 |
| C-NF-02 | Latency Overhead | Gateway 추가 지연을 측정·최소화한다. |
| C-NF-03 | Cost Controllability | 라우팅 정책으로 비용 상한을 관리할 수 있어야 한다. |
| C-NF-04 | Observability | 요청별 모델, 지연, 비용, 실패율을 추적한다. |

## 7. 시스템 구조

```text
Application
     ↓
AI Gateway
     ↓
Request Analyzer
     ↓
Routing Engine
     ↓
 ┌───┼────┐
 ↓   ↓    ↓
GPT Claude Gemini
 ↓   ↓    ↓
Evaluation
     ↓
Quality / Cost / Latency
     ↓
Analytics
```

## 8. 평가 예시

| 모델 | Quality | Latency | Cost |
| --- | ---: | ---: | ---: |
| GPT | 91 | 1.2s | $0.012 |
| Claude | 94 | 1.5s | $0.015 |
| Gemini | 89 | 0.8s | $0.007 |

## 9. 성공 지표

| 지표 | 설명 |
| --- | --- |
| Routing Accuracy | 요청 유형에 적합한 모델 선택 비율 |
| Fallback Success Rate | Fallback 후 정상 응답 비율 |
| Avg Latency | 요청 평균 지연 |
| Cost per Request | 요청당 평균 비용 |
| Quality Score | 평가 세트 기준 품질 점수 |

## 10. 범위 제외

- 프롬프트 보안 탐지·차단(Project D 범위)
- 파인튜닝 파이프라인
- 멀티모달(이미지/음성) 라우팅 초기 제외

## 11. 마일스톤

| Phase | 산출물 |
| --- | --- |
| M1 | Gateway + Provider Adapter |
| M2 | Request Analyzer + Routing Engine |
| M3 | Fallback |
| M4 | Evaluation + Analytics |

## 12. 가정 및 리스크

| 구분 | 내용 |
| --- | --- |
| 가정 | 최소 2개 이상의 LLM Provider API 접근이 가능하다. |
| 리스크 | Provider Rate Limit으로 Fallback이 연쇄 실패할 수 있다. |
| 리스크 | Quality 평가 기준의 주관성으로 비교 신뢰도가 저하될 수 있다. |

## 13. 의존성

- LLM Provider API (GPT, Claude, Gemini 등)
- Gateway / API 서버
- 로깅·메트릭 저장소
- Evaluation Dataset
