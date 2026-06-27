# Hybrid IR 평가 재설계 기준

이 폴더는 Hybrid IR과 Bedrock 파이프라인 평가를 다시 설계한 이유와 원칙을 설명합니다. 목적은 높은 수치를 만드는 것이 아니라, train 데이터와 held-out 평가를 섞지 않고, 검색 엔진과 LLM 파이프라인의 책임을 분리해서 검증하는 것입니다.

핵심 원칙은 다음과 같습니다.

```text
train_100_v2는 개발용 파이프라인 점검 데이터로만 사용한다.
최종 held-out 성능은 별도 고정 테스트셋에서 첫 실행 리포트를 보관한 뒤에만 말한다.
test 결과를 보고 prompt, alias, few-shot, domain pack을 고치면 안 된다.
```

## 재설계 배경

초기 평가 흐름은 train 데이터에서 나온 산출물과 평가 입력이 서로 가까워질 위험이 있었습니다. 이런 상태에서는 높은 점수가 나와도 다음 질문에 답하기 어렵습니다.

- 실제 일반화 성능인가?
- train set에 맞춘 산출물인가?
- 후보 검색이 좋아진 것인가, LLM 추출이 좋아진 것인가?
- 부정 증상과 호전 증상을 안전하게 배제한 것인가?

그래서 이 브랜치에서는 평가를 다음 구조로 재설계했습니다.

| 단계 | 목적 |
| --- | --- |
| `blueprint/` | 실제 문장 생성 전 증상군, 질문, 방언 layer, 상태 패턴 분포를 고정 |
| `train_100_v2/` | synthetic 환자 발화 100건을 렌더링하고 runtime artifact 후보 생성 |
| Track A | Bedrock 없이 후보 검색 recall만 측정 |
| Track B | 방언 RAG hint가 필요한 행에서만 검색되는지 측정 |
| Track C | Bedrock/LangGraph 통합 파이프라인의 최종 `matched_slots` 측정 |
| locked test | 최종 공개 성능 측정용. 현재 공개 수치와 분리해서 관리 |

## 제거한 범위

평가 신뢰도를 높이기 위해 아래 1차 cycle 산출물은 새 평가 흐름에서 제외했습니다.

- old `evaluation/generated/train_100`
- old `evaluation/train_100_blueprint`
- old `evaluation/train_100_training`
- old `evaluation/train_100_evaluation`
- old `evaluation/test_1000_blueprint`
- train-derived `backend/serverless/src/data/domain_packs/respiratory.json`
- train-derived `backend/serverless/src/data/fewshots/respiratory/*.json`

유지한 항목:

- application pipeline code
- question set structure
- current Gangwon dialect RAG pack
- reset marker documentation

## 데이터 설계 원칙

synthetic utterance는 전체 문진 완성도가 아니라 증상 추출과 후보 검색을 평가하기 위한 데이터입니다.

포함 대상:

- 초진 Q1 주호소
- 재진 Q3 경과/재발 응답
- active, persistent, improved, denied, mixed context

제외 대상:

- Q2 발생 시점 단독 응답
- Q4 의사에게 물어볼 질문
- 복약/영양제 중심 응답
- 실제 환자 원문

언어 분포:

- 표준어 50%
- 강원식 구어체 50%

강원식 구어체는 다시 source layer로 나눕니다.

| source layer | 의미 |
| --- | --- |
| `rag_pack_anchored` | 현재 강원 방언 RAG pack에 실제 anchor가 있는 행 |
| `clinical_colloquial` | 의료 현장에서 자연스러운 구어체이나 방언팩 근거로 주장하지 않는 행 |
| `light_dialect_style` | 지역 말투의 어미나 리듬만 반영한 행 |

이 구분 덕분에 "강원식 말투"와 "방언팩으로 근거화된 RAG hint"를 섞어 말하지 않을 수 있습니다.

## 문장 생성 원칙

좋은 synthetic row는 환자가 실제로 말할 법한 구어체여야 합니다.

권장:

- 환자답게 자연스러운 말투
- 부정 맥락과 호전 맥락을 명확히 표현
- 기술적 증상명은 필요한 경우 생활 표현으로 바꾸기
- 증상군과 상태 패턴을 blueprint와 맞추기

금지:

- 같은 문장 틀에서 증상명만 바꿔 대량 생성
- 모든 canonical symptom name을 직접 노출
- Q1/Q3 안에 Q2 기간 표현이나 Q4 질문을 과하게 섞기
- 방언 근거가 없는 행을 RAG-pack dialect라고 라벨링

## 산출물 provenance

train set에서 만들어지는 artifact는 근거를 남겨야 합니다.

필수 기록:

- source case id
- source quote
- proposed canonical symptom 또는 rule
- artifact type: domain pack, alias, few-shot, reviewer rule, scoring rule
- acceptance reason
- rejection reason

few-shot은 train set을 외우게 만드는 자료가 아니라, 출력 구조와 선택 기준을 보여주는 최소 예시여야 합니다.

## 평가 트랙

| Track | Bedrock 사용 | 측정하는 것 |
| --- | ---: | --- |
| Offline IR | 아니오 | 정답 canonical symptom이 후보 리스트에 들어오는지 |
| Dialect RAG sanity | 아니오 | 방언 pack 힌트가 anchor 행에서 검색되는지 |
| Pipeline integration | 예 | LangGraph, Bedrock extraction, schema validation, IR linking이 함께 작동하는지 |
| Product E2E | 예 | 실제 Q1~Q4 async 흐름과 UI 상태가 맞는지. 이 브랜치에서는 보조 정의만 제공 |

IR recall은 최종 F1이 아닙니다. 최종 추출 성능은 Pipeline integration track에서 보고, 최종 공개 성능은 locked test set에서 따로 측정해야 합니다.

## 현재 산출물

현재 핵심 산출물은 다음 위치에 있습니다.

| 위치 | 의미 |
| --- | --- |
| `blueprint/` | 100건 평가 행 분포와 품질 게이트 |
| `train_100_v2/` | 렌더링된 synthetic 문진 발화와 artifact build report |
| `reports/metrics_summary.json` | Track A/B/C 요약 지표 |
| `reports/pipeline_error_analysis.md` | 남은 mismatch의 정책 해석 |

## 제출 시 해석 기준

이 문서는 수치 결과보다 평가 설계의 정직성을 보여주는 문서입니다. 해커톤 제출에서는 다음처럼 설명하는 것이 좋습니다.

```text
Hybrid IR 평가는 train 데이터와 held-out 평가가 섞이지 않도록 재설계했다.
현재 공개 수치는 train_100_v2 개발용 평가 결과이며,
최종 성능 주장은 별도 locked test set의 첫 실행 리포트를 기준으로 분리 관리해야 한다.
```
