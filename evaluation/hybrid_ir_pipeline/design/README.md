# Hybrid IR 평가 재설계 기준

이 폴더는 오염 가능성이 있던 1차 train/evaluation cycle을 걷어낸 뒤, Hybrid IR과 Bedrock 파이프라인 평가를 다시 설계한 기준 문서입니다.

핵심은 간단합니다.

```text
train_100_v2는 런타임 산출물 생성과 파이프라인 점검에만 사용한다.
최종 held-out 성능은 별도 고정 테스트셋에서 첫 실행 리포트를 저장한 뒤 말한다.
test 결과를 본 뒤 prompt, alias, few-shot, domain pack을 고치면 안 된다.
```

## 재설계 배경

기존 1차 평가 흐름에는 train 데이터에서 얻은 정보가 평가와 다시 섞일 위험이 있었습니다. 이런 상태에서는 높은 수치가 나와도 실제 일반화 성능인지, train set에 맞춰진 결과인지 구분하기 어렵습니다.

그래서 이 브랜치에서는 평가를 다시 다음 구조로 나눴습니다.

| 단계 | 목적 |
| --- | --- |
| `blueprint/` | 실제 문장을 만들기 전 증상군, 질문, 방언 layer, 상태 패턴을 고정 |
| `train_100_v2/` | synthetic 환자 발화 100개를 렌더링하고 runtime artifact 후보 생성 |
| Track A | Bedrock 없이 후보 검색 품질만 확인 |
| Track B | 사투리 RAG pack anchor가 의도한 행에서 검색되는지 확인 |
| Track C | 실제 Bedrock/LangGraph 파이프라인 통합 동작 확인 |
| 향후 locked test | 최종 공개 성능 측정 |

## 제거한 범위

활성 평가 트리에서는 아래 1차 cycle 산출물을 제거했습니다.

- old `evaluation/generated/train_100`
- old `evaluation/train_100_blueprint`
- old `evaluation/train_100_training`
- old `evaluation/train_100_evaluation`
- old `evaluation/test_1000_blueprint`
- train-derived `backend/serverless/src/data/domain_packs/respiratory.json`
- train-derived `backend/serverless/src/data/fewshots/respiratory/*.json`

유지한 항목은 다음입니다.

- application pipeline code
- question set structure
- current Gangwon dialect RAG pack
- reset marker documentation

## 데이터 설계 원칙

synthetic utterance는 전체 문진 완성도가 아니라 증상 추출과 후보 검색을 점검하기 위한 데이터입니다.

포함 대상:

- 초진 Q1 주호소
- 재진 Q3 경과/재발 답변

제외 대상:

- Q2 발생 시점 단독 답변
- Q4 의사에게 물어볼 질문
- 약물/영양제 질문 중심 답변

언어 분포:

- 표준어 50%
- 강원체 50%

강원체 행은 다시 source layer를 나눕니다.

| source layer | 의미 |
| --- | --- |
| `rag_pack_anchored` | 현재 강원 방언 RAG pack에 실제 anchor가 있는 행 |
| `clinical_colloquial` | 자연스러운 의료 구어체지만 RAG pack 근거로 주장하지 않는 행 |
| `light_dialect_style` | 지역 말투나 어미 느낌만 반영한 행 |

이 구분 덕분에 "강원체 50개"를 모두 "RAG pack으로 근거화된 사투리"라고 과장하지 않을 수 있습니다.

## 문장 생성 원칙

좋은 synthetic row는 환자가 실제로 말할 법한 구어체여야 합니다.

권장:

- 환자답게 자연스러운 말투
- 흔한 표현은 그대로 사용
- 기술적 증상명은 필요한 경우 생활 표현으로 풀어쓰기
- 증상군과 상태 패턴이 blueprint에 맞게 드러나기

피해야 할 것:

- 같은 문장 틀에 증상명만 바꿔 끼우기
- 모든 canonical symptom name을 직접 노출하기
- Q1/Q3 안에 Q2 기간, Q4 질문, 약물 질문을 과하게 섞기
- 방언 근거가 없는데 RAG-pack dialect라고 라벨링하기

## 산출물 provenance

train에서 파생되는 artifact는 근거를 남겨야 합니다.

필수 기록:

- source case id
- source quote
- proposed canonical symptom 또는 rule
- artifact type: domain pack, alias, few-shot, reviewer rule, scoring rule
- acceptance reason
- rejection reason

few-shot은 train set을 외우게 만드는 자료가 아니라, 출력 구조와 애매한 케이스 처리 방식을 보여주는 대표 예시여야 합니다.

## 평가 트랙

| Track | Bedrock 사용 | 측정하는 것 |
| --- | ---: | --- |
| Offline IR | 아니오 | 정답 canonical symptom이 후보 리스트에 들어오는지 |
| Dialect RAG sanity | 아니오 | 방언 pack 힌트가 anchor 행에서 검색되는지 |
| Pipeline integration | 예 | LangGraph, Bedrock extraction, schema validation, IR linking이 함께 동작하는지 |
| Product E2E | 예 | 실제 Q1~Q4 async 흐름과 UI 상태가 맞는지 |

IR recall은 최종 F1이 아닙니다. 최종 추출 성능은 Pipeline integration track, 그중에서도 locked test set에서 측정해야 합니다.

## 현재 산출물

현재 승인된 blueprint는 `evaluation/hybrid_ir_pipeline/blueprint/`에 있습니다.

blueprint가 고정하는 항목:

- symptom-group distribution
- dialect source-layer counts
- direct-name versus paraphrase policy
- negative and resolved symptom ratios
- difficulty levels
- validation checks before rendering

## 제출 시 해석 기준

이 문서는 수치 결과보다 평가 설계의 신뢰성을 보여주는 문서입니다. 해커톤 제출에서는 다음처럼 설명하는 것이 좋습니다.

```text
Hybrid IR 평가는 train 데이터와 held-out 평가를 섞지 않기 위해 재설계했다.
현재 공개 수치는 train_100_v2 점검 결과이며,
향후 locked test set의 첫 실행 리포트를 별도 보관해야 최종 성능으로 말할 수 있다.
```
