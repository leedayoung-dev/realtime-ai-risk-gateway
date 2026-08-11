# PRD — Real-time News Credibility Detection

| 항목 | 내용 |
| --- | --- |
| 프로젝트 코드 | Project A |
| 문서 버전 | 1.0 |
| 상태 | Draft |
| 연관 문서 | `../초안.md` |

---

## 1. 개요

뉴스 기사, 출처, 외부 증거, 확산 패턴을 실시간 분석하여 시점별 신뢰도 위험도(Credibility Risk)를 산출하는 시스템이다.

Fake/Real 이진 분류가 아니라, 확보된 정보 기준의 **검증 필요도**를 산출한다.

## 2. 문제 정의

| 구분 | 내용 |
| --- | --- |
| 문제 | 뉴스의 신뢰성 검증은 사후 팩트체크에 의존하며, 확산 초기에 위험을 정량화하기 어렵다. |
| 영향 | 미검증 정보가 빠르게 확산되고, 검증 우선순위 결정이 지연된다. |
| 기회 | 실시간 스트리밍과 증거 기반 분석을 결합하면 조기 위험 탐지가 가능하다. |

## 3. 목표 및 비목표

### 목표

- 뉴스 수집부터 위험도 산출·API·대시보드까지 End-to-End 파이프라인 구축
- Claim 단위 증거 수집 및 Feature 기반 위험도 산출
- 시간에 따른 Risk Score 갱신 및 Early Detection 성능 측정

### 비목표

- Fake/Real 절대 판정 시스템 구축
- 공유량만으로 Fake를 판별하는 모델
- 모든 언론사·플랫폼에 대한 완전 자동화 팩트체크

## 4. 사용자 및 이해관계자

| 역할 | 니즈 |
| --- | --- |
| 팩트체크 담당자 | 검증 우선순위가 높은 기사·Claim 식별 |
| 미디어 모니터 | 실시간 위험도 추이 확인 |
| 플랫폼 운영자 | API를 통한 위험도 조회 및 연동 |

## 5. 기능 요구사항

### 5.1 뉴스 수집 및 스트리밍

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| A-F-01 | 뉴스 소스를 수집하여 Kafka로 발행한다. | P0 |
| A-F-02 | PySpark Streaming으로 실시간 처리한다. | P0 |

### 5.2 Claim Extraction

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| A-F-03 | 기사를 검증 가능한 Claim 단위로 분리한다. | P0 |
| A-F-04 | Claim별 식별자와 원문 매핑을 유지한다. | P0 |

### 5.3 Evidence Retrieval

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| A-F-05 | Claim별 Supporting / Contradicting / Official Evidence를 수집한다. | P0 |
| A-F-06 | 증거 출처 및 수집 시각을 기록한다. | P1 |

### 5.4 Feature 및 위험도

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| A-F-07 | Source Analysis Feature를 산출한다. | P0 |
| A-F-08 | Propagation Feature(Velocity, Acceleration, Burst, Engagement)를 산출한다. | P0 |
| A-F-09 | Feast + Redis에 Feature를 저장·조회한다. | P0 |
| A-F-10 | ML/NLP 모델로 Credibility Risk Score를 산출한다. | P0 |
| A-F-11 | 시간에 따라 Risk Score를 갱신한다. | P0 |

### 5.5 서빙 및 시각화

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| A-F-12 | FastAPI로 위험도·Claim·증거 조회 API를 제공한다. | P0 |
| A-F-13 | Dashboard에서 기사별 위험도 추이를 시각화한다. | P1 |

## 6. 비기능 요구사항

| ID | 항목 | 기준 |
| --- | --- | --- |
| A-NF-01 | Latency | 스트리밍 이벤트 수신 후 Risk 갱신 SLA 정의 및 준수 |
| A-NF-02 | Scalability | Kafka 기반 수평 확장이 가능해야 한다. |
| A-NF-03 | Traceability | Claim·Evidence·Score 산출 경로를 추적 가능해야 한다. |
| A-NF-04 | Observability | 파이프라인 지연, 실패율, 처리량을 모니터링한다. |

## 7. 시스템 구조

```text
Real News
    ↓
News Collector
    ↓
Kafka
    ↓
PySpark Streaming
    ↓
Claim Extraction
    ↓
Evidence Retrieval
    ↓
Feature Engineering
    ↓
Feast + Redis
    ↓
ML / NLP Models
    ↓
Credibility Risk
    ↓
FastAPI
    ↓
Dashboard
```

## 8. 데이터 및 Feature

| 영역 | 항목 |
| --- | --- |
| Claim | 주장 텍스트, 위치, 추출 시각 |
| Evidence | Supporting / Contradicting / Official |
| Source | 언론사 신뢰도, 검증 이력 |
| Propagation | Share Velocity, Acceleration, Burst, Engagement Pattern |
| Temporal | 시점별 Risk Score |

## 9. 성공 지표

| 지표 | 설명 |
| --- | --- |
| Early Detection Rate | 공식 팩트체크 이전 위험 탐지 비율 |
| Risk Update Latency | Risk Score 갱신 지연 |
| Evidence Coverage | Claim당 수집 증거 수·유형 커버리지 |
| Ranking Quality | 검증 우선순위와 실제 검증 결과의 정합성 |

## 10. 범위 제외

- 실시간 소셜 미디어 전수 수집
- 법적 책임 판정 또는 콘텐츠 자동 삭제
- 다국어 전체 지원(초기에는 단일 언어 우선)

## 11. 마일스톤

| Phase | 산출물 |
| --- | --- |
| M1 | Collector + Kafka + Streaming 기반 파이프라인 |
| M2 | Claim Extraction + Evidence Retrieval |
| M3 | Feature Store + Risk Model |
| M4 | FastAPI + Dashboard + Early Detection 평가 |

## 12. 가정 및 리스크

| 구분 | 내용 |
| --- | --- |
| 가정 | 뉴스·증거 소스 API 또는 공개 데이터 접근이 가능하다. |
| 리스크 | 증거 품질 저하 시 Risk Score 신뢰도가 하락한다. |
| 리스크 | Propagation 지표가 인기도와 혼동되어 오탐이 증가할 수 있다. |

## 13. 의존성

- Kafka, PySpark Streaming
- Feast, Redis
- FastAPI
- NLP/ML 모델 학습·서빙 환경
