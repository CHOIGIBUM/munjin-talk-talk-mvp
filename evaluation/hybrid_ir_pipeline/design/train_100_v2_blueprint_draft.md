# Train 100 v2 Blueprint Draft

이 문서는 `train_100_v2` 데이터셋을 만들기 전 작성한 설계 초안입니다. 생성된 평가 데이터나 성능 결과가 아니며, 어떤 기준으로 100건의 synthetic 문진 발화를 만들 것인지 정의합니다.

## Scope

`train_100_v2`는 증상 추출 보조 계층과 Hybrid IR 후보 검색을 점검하기 위한 개발용 데이터입니다.

포함:

- Initial visit Q1: chief complaint
- Follow-up visit Q3: recurrence, persistence, worsening, improvement, or return of symptoms

제외:

- Q2 onset timing
- Q4 patient questions to the doctor
- 별도 medication-context task가 없는 복약력 중심 응답
- 기간 표현 자체를 평가하는 별도 task가 없는 exact duration expression

## Required Counts

총 row 수는 100건입니다.

방문/질문 분포:

| Visit | Question | Count |
| --- | --- | ---: |
| Initial | Q1 chief complaint | 50 |
| Follow-up | Q3 recurrence/course | 50 |

언어 스타일 분포:

| Language Style | Count |
| --- | ---: |
| Standard Korean | 50 |
| Gangwon-style Korean | 50 |

교차 분포:

| Visit/Question | Standard | Gangwon-style |
| --- | ---: | ---: |
| Initial Q1 | 25 | 25 |
| Follow-up Q3 | 25 | 25 |

## Dialect Source Layers

모든 Gangwon-style row는 source layer를 가져야 합니다.

| Layer | Target Count | Rule |
| --- | ---: | --- |
| `rag_pack_anchored` | 10 | 현재 강원 방언팩에 실제로 존재하는 표현만 사용 |
| `clinical_colloquial` | 25 | 자연스러운 환자 구어체이나 방언팩 근거로 주장하지 않음 |
| `light_dialect_style` | 15 | 지역 말투의 어미와 억양 느낌만 반영 |

이 설계의 의도는 방언 RAG 성능을 과장하지 않는 것입니다. 강원식 말투라고 해서 모두 방언팩 기반 hint가 있어야 하는 것은 아닙니다. Track B에서는 `rag_pack_anchored` 10건만 기대 hint 검색 대상으로 봅니다.

## Symptom Group Distribution

첫 draft는 호흡기 및 이비인후과 인접 증상 추출을 넓게 커버하되, 하나의 증상군에 과적합하지 않도록 설계했습니다.

| Group | Count |
| --- | ---: |
| Upper airway and common cold-like symptoms | 18 |
| Cough, phlegm, and lower-airway symptoms | 20 |
| Dyspnea, chest discomfort, and urgent respiratory clues | 18 |
| Fever, chills, fatigue, body ache, and systemic course | 14 |
| Voice, swallowing, throat, eye, and ENT-adjacent symptoms | 10 |
| Dizziness, palpitation, edema, and overlapping red-flag context | 10 |
| GI or nonspecific context that may confuse respiratory extraction | 10 |

이 항목은 설계 bucket이지 최종 canonical label이 아닙니다. canonical symptom name은 domain pack과 평가 기준에서 별도 고정합니다.

## Expression Policy

환자가 흔히 직접 말하는 표현은 그대로 등장해도 됩니다.

- cough
- runny nose
- stuffy nose
- fever
- phlegm
- throat pain
- dizziness

환자가 기술 용어로 말하기 어려운 개념은 생활 표현으로 숨겨야 합니다.

- dyspnea
- wheezing
- hemoptysis
- purulent sputum
- edema
- dysphagia
- chest tightness

목표 분포:

| Expression Type | Count |
| --- | ---: |
| Direct common patient word | 35 |
| Lay paraphrase | 45 |
| Technical concept hidden behind natural description | 20 |

## Status Pattern Distribution

| Status Pattern | Count | Meaning |
| --- | ---: | --- |
| `active_current` | 45 | 지금 증상이 있음 |
| `recurrent_or_persistent` | 25 | 재진 Q3에서 증상이 지속, 반복, 재발 |
| `improved_or_resolved` | 10 | 호전 또는 해소되어 현재 active complaint로 올리면 안 됨 |
| `denied_negative_context` | 15 | 증상이 명시적으로 없음 |
| `mixed_context` | 5 | 한 증상은 있고 다른 증상은 없거나 호전됨 |

이 분포는 active symptom card 정책을 검증하기 위해 필요합니다. 특히 `improved_or_resolved`와 `denied_negative_context`는 recall만 높이려는 시스템에서 false positive를 만들기 쉬운 영역입니다.

## Leakage Rules

renderer가 해서는 안 되는 일:

- old `train_100` utterance 복사
- old `test_1000` blueprint row 복사
- Q2-style onset phrase를 main content로 사용
- Q4-style doctor question을 target sentence로 사용
- 같은 문장 frame에서 증상명만 반복 교체
- IR이 쉬워지도록 canonical label을 억지로 삽입

renderer가 해도 되는 일:

- 짧은 구어체 사용
- 자연스럽다면 불완전한 문법 사용
- `light_dialect_style` 행에서 가벼운 지역 어미 사용
- 명시적으로 배정된 negative context 포함

## Quality Gate Before Rendering

환자 발화 생성 전 blueprint는 다음 조건을 통과해야 합니다.

- exactly 100 planned rows
- exactly 50 Q1 and 50 Q3
- exactly 50 standard and 50 Gangwon-style
- no Q2 or Q4 target rows
- every Gangwon-style row has a source layer
- every row has expected gold symptoms and expected negative symptoms
- every row has one status pattern
- every row has an expression policy

## Quality Gate After Rendering

LLM 렌더링 이후 row를 거절해야 하는 경우:

- spoken Korean처럼 들리지 않음
- 환자 답변이 아니라 의사에게 하는 질문임
- Q2 timing이 본문을 지배함
- 복약이 main answer가 됨
- gold symptom을 텍스트에서 추론할 수 없음
- negative symptom이 present로 표현됨
- `technical_hidden` row에서 기술 용어가 직접 노출됨
- 방언 layer evidence를 과장함

## Artifact Build Rule

accepted `train_100_v2`는 다음 후보 산출물을 만들 수 있습니다.

- clean domain pack candidates
- alias candidates
- few-shot candidates
- reviewer or safety rules

모든 accepted artifact는 source case id와 사람이 읽을 수 있는 acceptance reason을 가져야 합니다.

`test_1000_v2` 또는 locked held-out test에서 artifact를 만들면 안 됩니다.
