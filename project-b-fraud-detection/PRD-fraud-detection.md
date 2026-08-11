# PRD — Real-time Fraud & Suspicious Behavior Detection

| 항목 | 내용 |
| --- | --- |
| 프로젝트 코드 | Project B |
| 문서 버전 | 1.0 |
| 상태 | Draft |
| 연관 문서 | `../초안.md` |

---

## 1. 개요

중고거래 환경을 가정하여 사용자 행동, 게시글, 거래, 채팅 이벤트를 실시간 분석하고 사기 가능성이 높은 행동을 탐지하는 시스템이다.

## 2. 문제 정의

| 구분 | 내용 |
| --- | --- |
| 문제 | 사기·이상 행동은 거래 완료 이후 신고로 확인되는 경우가 많다. |
| 영향 | 피해 발생 후 대응이 지연되고, 유사 패턴이 반복된다. |
| 기회 | 실시간 이벤트 Feature와 이상탐지로 사전 차단·검토가 가능하다. |

## 3. 목표 및 비목표

### 목표

- 사용자·리스팅·행동·네트워크 Feature 기반 Fraud Risk 산출
- Supervised 모델과 Anomaly Detection의 성능 비교
- Risk Factor 설명 가능한 출력 제공

### 비목표

- 실제 결제/정산 시스템 연동
- 법적 사기 확정 판정
- 모든 중고거래 플랫폼 규칙의 완전 복제

## 4. 사용자 및 이해관계자

| 역할 | 니즈 |
| --- | --- |
| Trust & Safety 담당자 | 고위험 사용자·거래 우선 검토 |
| 운영자 | Risk Score 및 Factor 기반 대응 |
| 데이터/ML 엔지니어 | 모델 비교·모니터링 |

## 5. 기능 요구사항

### 5.1 이벤트 수집

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| B-F-01 | Login, Listing, Chat, Transaction, Report 이벤트를 Kafka로 수집한다. | P0 |
| B-F-02 | 이벤트 스키마와 사용자 식별자를 표준화한다. | P0 |

### 5.2 Feature Engineering

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| B-F-03 | User Feature를 산출한다. (`account_age`, `transaction_count`, `report_count`) | P0 |
| B-F-04 | Listing Feature를 산출한다. (`price_deviation`, `listing_frequency`, `duplicate_listing_ratio`) | P0 |
| B-F-05 | Behavior Feature를 산출한다. (`messages_per_5m`, `listing_burst`, `new_users_contacted`, `external_contact_attempt`) | P0 |
| B-F-06 | Network Feature(사용자 간 연결)를 산출한다. | P1 |

### 5.3 모델 및 점수화

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| B-F-07 | Supervised 모델(LightGBM)로 Fraud Risk를 산출한다. | P0 |
| B-F-08 | Anomaly Detection(Isolation Forest, Autoencoder, Statistical)을 구현한다. | P0 |
| B-F-09 | 두 접근법의 성능을 비교 평가한다. | P0 |
| B-F-10 | Risk Factor별 기여도(HIGH/MEDIUM 등)를 제공한다. | P0 |

### 5.4 서빙

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| B-F-11 | 사용자·거래 단위 Risk 조회 API를 제공한다. | P0 |
| B-F-12 | 고위험 알림 또는 대시보드 연동 인터페이스를 제공한다. | P1 |

## 6. 비기능 요구사항

| ID | 항목 | 기준 |
| --- | --- | --- |
| B-NF-01 | Latency | 이벤트 유입 후 Risk 갱신 지연을 측정·관리한다. |
| B-NF-02 | Explainability | Risk Factor를 해석 가능한 형태로 제공한다. |
| B-NF-03 | Privacy | 개인식별 정보는 최소 수집·마스킹 정책을 적용한다. |
| B-NF-04 | Robustness | 이벤트 누락·지연 상황에서도 점수 산출이 가능해야 한다. |

## 7. 시스템 구조

```text
User Events (Login / Listing / Chat / Transaction / Report)
    ↓
Kafka
    ↓
Feature Engineering
    ↓
┌───────────────┬────────────────────┐
↓               ↓                    ↓
LightGBM   Isolation Forest   Autoencoder / Stats
↓               ↓                    ↓
└───────────────┴────────────────────┘
                ↓
          Fraud Risk + Factors
                ↓
           API / Dashboard
```

## 8. 데이터

```text
User
 ├── Login
 ├── Listing
 ├── Chat
 ├── Transaction
 └── Report
```

| Feature 그룹 | 예시 |
| --- | --- |
| User | account_age, transaction_count, report_count |
| Listing | price_deviation, listing_frequency, duplicate_listing_ratio |
| Behavior | messages_per_5m, listing_burst, new_users_contacted, external_contact_attempt |
| Network | 사용자 간 연결 관계 |

## 9. 성공 지표

| 지표 | 설명 |
| --- | --- |
| Precision@K | 상위 위험 사용자 중 실제 사기/신고 비율 |
| Recall | 사기 케이스 탐지율 |
| False Positive Rate | 정상 사용자 오탐률 |
| Time-to-Detect | 이상 행동 발생 후 탐지까지 소요 시간 |
| Model Comparison Gap | Supervised vs Anomaly Detection 성능 차이 |

## 10. 출력 예시

```text
Fraud Risk                 91
Listing Burst              HIGH
Price Anomaly              HIGH
Chat Pattern               HIGH
Account Age                HIGH
Report History             MEDIUM
```

## 11. 범위 제외

- 실제 자금 동결·계정 제재 자동화
- 외부 신용평가 기관 연동
- 이미지/음성 기반 사기 탐지(초기 범위 제외)

## 12. 마일스톤

| Phase | 산출물 |
| --- | --- |
| M1 | 이벤트 스키마 + Kafka 수집 |
| M2 | Feature Pipeline |
| M3 | Supervised + Anomaly 모델 |
| M4 | Risk API + 비교 평가 리포트 |

## 13. 가정 및 리스크

| 구분 | 내용 |
| --- | --- |
| 가정 | 라벨(신고·사기 확정) 데이터가 일부 존재하거나 시뮬레이션 가능하다. |
| 리스크 | 라벨 희소성으로 Supervised 성능이 제한될 수 있다. |
| 리스크 | Network Feature 구축 비용이 과도할 수 있다. |

## 14. 의존성

- Kafka
- Feature Store 또는 동등 저장소
- LightGBM 및 Anomaly Detection 라이브러리
- API 서빙 환경
