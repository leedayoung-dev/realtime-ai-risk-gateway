# PRD — AI Security Gateway & Monitoring

| 항목 | 내용 |
| --- | --- |
| 프로젝트 코드 | Project D |
| 문서 버전 | 1.0 |
| 상태 | Draft |
| 연관 문서 | `../초안.md` |

---

## 1. 개요

기업 환경의 AI 서비스를 가정하고, 사용자와 LLM 사이에 AI Security Gateway를 구축한다. 통제된 환경에서 AI 보안 위협을 재현하고, 탐지·분류·차단·모니터링 체계를 설계한다.

공격 기법 개발이 목적이 아니라, 방어 시스템의 유효성 검증이 목적이다.

## 2. 문제 정의

| 구분 | 내용 |
| --- | --- |
| 문제 | LLM 서비스는 Prompt Injection, Jailbreak, 민감정보 유출 등 기존 웹 보안과 다른 위협을 포함한다. |
| 영향 | WAF·API Gateway만으로는 AI 특화 위험을 충분히 통제하기 어렵다. |
| 기회 | Security Gateway + Policy + Monitoring으로 방어 사이클을 구축할 수 있다. |

### 대상 위협

| 위협 | 설명 |
| --- | --- |
| Prompt Injection | 지시문 탈취·우회 |
| Jailbreak | 안전 정책 우회 |
| System Prompt Extraction | 시스템 프롬프트 유출 |
| Sensitive Data Exposure | 민감정보 노출 |
| Credential Leakage | 자격증명 유출 |
| Excessive Tool Usage | Tool 남용 |
| Abnormal API Usage | 비정상 API 사용 |
| Indirect Prompt Injection | 외부 문서 경유 주입 |

## 3. 목표 및 비목표

### 목표

- Prompt Security, DLP, Abuse Detection을 Gateway에 통합
- Policy Engine 기반 ALLOW / REVIEW / BLOCK 결정
- 다층 Detection(Rule + ML + LLM Judge) 및 비교 실험
- 보안 이벤트 모니터링 및 사용자 Risk Profiling
- Agent Tool Permission 정책 확장

### 비목표

- 실서비스 대상 공격 수행
- 실제 개인정보·자격증명 사용
- 공격 성공을 목적화한 Red Team 도구 배포

## 4. 사용자 및 이해관계자

| 역할 | 니즈 |
| --- | --- |
| AI Security Engineer | 위협 탐지·차단 정책 설계 |
| SOC / 운영자 | 이벤트 모니터링 및 사용자 Risk 대응 |
| Platform Engineer | Gateway·라우팅과의 연동 |
| Compliance | DLP 및 정책 준수 증적 |

## 5. 기능 요구사항

### 5.1 Security Gateway

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-01 | 사용자 요청을 AI Security Gateway에서 선처리한다. | P0 |
| D-F-02 | Prompt Security, DLP, Abuse Detection을 병렬 수행한다. | P0 |
| D-F-03 | Policy Engine이 ALLOW / REVIEW / BLOCK을 결정한다. | P0 |
| D-F-04 | ALLOW된 요청만 LLM Router로 전달한다. | P0 |
| D-F-05 | 응답에 대해 Output Guard(PII/Leakage/Policy Check)를 수행한다. | P0 |

### 5.2 Prompt Security

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-06 | Normal / Direct Injection / System Prompt Extraction / Indirect Injection 테스트셋을 구성한다. | P0 |
| D-F-07 | Injection 및 Jailbreak를 탐지한다. | P0 |

### 5.3 Detection Engine

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-08 | Layer 1 Rule 기반 탐지를 구현한다. | P0 |
| D-F-09 | Layer 2 ML Classifier를 구현한다. | P0 |
| D-F-10 | Layer 3 LLM Judge를 구현한다. | P1 |
| D-F-11 | Rule + ML + LLM Judge Score로 Risk Score를 산출한다. | P0 |

### 5.4 DLP

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-12 | 입·출력에서 PII 및 Credential을 탐지한다. | P0 |
| D-F-13 | 정책에 따라 Allow / Mask / Block / Review로 처리한다. | P0 |
| D-F-14 | Synthetic Data만 사용하여 검증한다. | P0 |

| 데이터 | 처리 예시 |
| --- | --- |
| Phone Number | MASK |
| API Key | BLOCK |
| Internal Document | REVIEW |

### 5.5 Policy Engine

| 조건 | 행동 |
| --- | --- |
| Prompt Injection Risk > 80 | BLOCK |
| PII Detected | MASK |
| Risk 50 ~ 80 | HUMAN REVIEW |
| Risk < 50 | ALLOW |

### 5.6 Agent Security

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-15 | Agent Tool Call에 Permission을 적용한다. | P1 |
| D-F-16 | 위험 Tool Call을 차단한다. | P1 |

| Tool | Permission |
| --- | --- |
| Search | ALLOW |
| DB Read | ALLOW |
| DB Write | DENY |
| Email | REVIEW |
| External API | DENY |

### 5.7 Monitoring 및 Risk Profiling

| ID | 요구사항 | 우선순위 |
| --- | --- | --- |
| D-F-17 | 보안 이벤트를 Kafka로 수집한다. | P0 |
| D-F-18 | Risk Engine 및 Dashboard를 제공한다. | P0 |
| D-F-19 | 사용자별 행동 패턴 기반 Risk Profiling을 수행한다. | P1 |

## 6. 비기능 요구사항

| ID | 항목 | 기준 |
| --- | --- | --- |
| D-NF-01 | Detection Latency | 탐지 소요 시간을 측정·관리한다. |
| D-NF-02 | Block Latency | 차단 결정까지 지연을 최소화한다. |
| D-NF-03 | Safety | 실개인정보·실자격증명을 사용하지 않는다. |
| D-NF-04 | Auditability | 탐지·정책·차단 이력을 추적 가능해야 한다. |

## 7. 시스템 구조

```text
User → AI Application → AI SECURITY GATEWAY
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
  Prompt Security            DLP             Abuse Detection
         └────────────────────┼────────────────────┘
                              ▼
                        Policy Engine
                     ALLOW / REVIEW / BLOCK
                              │
                         LLM Router
                              ▼
                        Output Guard
                              ▼
                             User
```

모니터링:

```text
AI Gateway → Kafka → Security Analytics → Risk Engine → Redis/DB → Dashboard
```

## 8. 평가 및 실험

### 방어 검증 목표

공격 성공률 감소와 False Positive를 함께 평가한다.

| 단계 | 구성 | Attack Success Rate (예시) |
| --- | --- | ---: |
| Baseline | Security Gateway 없음 | 72% |
| Layer 1 | Rule-based | 43% |
| Layer 2 | ML Detection | 18% |
| Layer 3 | Policy + ML + LLM Judge | 7% |

### 비교 실험

| Experiment | 구성 |
| --- | --- |
| 1 | Rule-based |
| 2 | ML-based |
| 3 | LLM-based |
| 4 | Rule + ML |
| 5 | Rule + ML + LLM Judge |

비교 항목: Detection Rate, Latency, False Positive, Cost

### 평가 지표

| 지표 | 설명 |
| --- | --- |
| Attack Detection Rate | 공격 탐지율 |
| Attack Success Rate | 방어 우회 성공률 |
| False Positive Rate | 정상 요청 오탐률 |
| False Negative Rate | 공격 미탐률 |
| Detection Latency | 탐지 소요 시간 |
| Block Latency | 차단 소요 시간 |
| PII Detection Recall | 민감정보 탐지율 |
| Policy Accuracy | 정책 판단 정확도 |

## 9. 성공 지표

- Baseline 대비 Attack Success Rate 유의미한 감소
- False Positive Rate 허용 범위 내 유지
- Detection/Block Latency SLA 충족
- 방어 전략별 비교 실험 리포트 산출

## 10. 범위 제외

- 실운영 시스템 대상 공격
- 실제 PII/Credential 데이터셋
- 물리 보안 또는 인프라 침투 테스트

## 11. 마일스톤

| Phase | 산출물 |
| --- | --- |
| M1 | AI Security Gateway + Rule Detection |
| M2 | DLP + Policy Engine |
| M3 | ML / LLM Judge + 비교 실험 |
| M4 | Monitoring + Risk Profiling |
| M5 | Agent Security 확장 |

## 12. 가정 및 리스크

| 구분 | 내용 |
| --- | --- |
| 가정 | 통제된 테스트셋과 Synthetic Data로 검증한다. |
| 리스크 | LLM Judge 비용·지연이 과도할 수 있다. |
| 리스크 | Rule 과다 시 False Positive가 증가한다. |
| 리스크 | Indirect Injection 재현 난이도가 높다. |

## 13. 의존성

- Project C LLM Gateway와의 연동 가능 구조
- Kafka, Redis/DB
- Detection 모델 및 LLM Judge
- Dashboard / Analytics 스택

## 14. 핵심 산출물

방어 사이클 자체를 프로젝트 산출물로 한다.

```text
Threat
  → Controlled Attack Scenario
  → Detection
  → Risk Assessment
  → Policy
  → Allow / Review / Block
  → Monitoring
  → Evaluation
  → Defense Improvement
```
