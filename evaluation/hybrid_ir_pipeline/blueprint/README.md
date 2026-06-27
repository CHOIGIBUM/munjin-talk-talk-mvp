# Train 100 v2 Blueprint 설계 문서

이 폴더는 `train_100_v2`를 만들기 전, "어떤 종류의 평가 행 100건을 만들 것인가"를 고정한 row-level blueprint입니다. 실제 환자 발화 텍스트가 아니라, 렌더링 단계에서 생성해야 할 증상 조합, 질문 유형, 방언 source layer, 상태 패턴을 정의합니다.

## 목적

blueprint의 역할은 데이터셋을 무작위로 만들지 않았음을 보여주는 것입니다. 해커톤 심사 기준에서는 단순히 "100건을 테스트했다"보다 "100건이 어떤 기준으로 분포되었고, 어떤 편향을 피하려 했는가"가 더 중요합니다.

이 단계에는 실제 환자 문장이나 Bedrock 출력문을 넣지 않습니다. 증상 조합과 생성 조건만 고정하여, 이후 렌더링 데이터가 특정 문장 패턴이나 특정 증상군에 과도하게 치우치지 않도록 합니다.

## 파일

| 파일 | 역할 |
| --- | --- |
| `distribution_plan.json` | 전체 분포와 생성 규칙 |
| `case_blueprint.schema.json` | blueprint row의 JSON schema |
| `case_blueprint.jsonl` | 100건 planned row |
| `quality_gate_report.json` | blueprint 검증 요약 |
| `build_blueprint.py` | blueprint 재생성 스크립트 |

## 고정 분포

`distribution_plan.json` 기준입니다.

| 항목 | 분포 |
| --- | --- |
| 방문/질문 | 초진 Q1 50건, 재진 Q3 50건 |
| 언어 스타일 | 표준어 50건, 강원식 구어체 50건 |
| 방언 source layer | rag_pack_anchored 10건, clinical_colloquial 25건, light_dialect_style 15건, none 50건 |
| 표현 정책 | direct_common 35건, lay_paraphrase 45건, technical_hidden 20건 |
| 상태 패턴 | active_current 45건, recurrent_or_persistent 25건, improved_or_resolved 10건, denied_negative_context 15건, mixed_context 5건 |

## source layer 의미

| layer | 의미 | 해석 기준 |
| --- | --- | --- |
| `rag_pack_anchored` | 현재 강원 방언팩에 실제 anchor가 있는 행 | Track B에서 기대 힌트 검색 대상으로 사용 |
| `clinical_colloquial` | 자연스러운 의료 구어체이나 방언팩 근거로 주장하지 않는 행 | "강원식 말투"이지 "RAG 근거 방언"이라고 과장하지 않음 |
| `light_dialect_style` | 어미나 리듬만 지역 말투에 가까운 행 | 방언 힌트가 없어도 실패가 아님 |
| `none` | 표준어 행 | 방언 RAG 노이즈가 없어야 함 |

이 구분은 중요합니다. 강원식 표현 50건 전체를 방언팩 기반 RAG 성공 사례로 주장하지 않고, 실제 pack anchor가 있는 10건만 `rag_pack_anchored`로 분리합니다.

## 범위

포함:

- 초진 Q1 주호소
- 재진 Q3 경과/재발 응답
- 호흡기/이비인후과 인접 증상
- 부정 맥락, 호전 맥락, mixed context

제외:

- Q2 발생 시점 단독 응답
- Q4 의사에게 물어볼 질문
- 복약/영양제 중심 응답
- 실제 환자 개인정보나 운영 데이터

## 품질 기준

`quality_gate_report.json`의 `passed`가 `true`여야 렌더링 단계로 넘어갑니다. 검증 기준은 다음과 같습니다.

- 총 100건
- Q1 50건, Q3 50건
- 표준어 50건, 강원식 구어체 50건
- 모든 강원식 행에 source layer 존재
- 모든 행에 gold symptom과 negative symptom 필드 존재
- 모든 행에 상태 패턴 존재
- `rag_pack_anchored` 행은 실제 방언팩 anchor를 근거로 함

## 제출 시 해석 기준

blueprint는 성능 결과가 아니라 데이터 설계 근거입니다. 해커톤 문서에서는 다음처럼 설명하는 것이 좋습니다.

```text
train_100_v2는 렌더링 전에 blueprint로 분포를 고정했다.
초진/재진, 표준어/강원식 구어체, 방언팩 anchor, 증상군, 상태 패턴을 먼저 나누어
특정 증상이나 특정 말투에만 맞춘 평가가 되지 않도록 설계했다.
```

아래처럼 표현하면 안 됩니다.

- blueprint 통과를 모델 성능으로 해석
- 모든 강원식 행이 방언 RAG로 근거화되었다고 주장
- Q2/Q4까지 포함한 전체 문진 성능 평가로 표현
