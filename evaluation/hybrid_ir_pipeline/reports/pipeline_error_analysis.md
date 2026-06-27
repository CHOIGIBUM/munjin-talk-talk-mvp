# Pipeline Error Analysis

Dataset: `evaluation/hybrid_ir_pipeline/train_100_v2/train_100_v2.jsonl`

이 문서는 held-out 최종 성능 리포트가 아닙니다. `train_100_v2` 기반 파이프라인 점검 결과를 사용해 후보 검색 품질과 Bedrock 추출/링킹 품질을 분리 해석하기 위한 오류 분석입니다.

## Final Summary

| 항목 | 값 |
| --- | ---: |
| Completed rows | 100/100 |
| Schema/runtime failures | 0 |
| Source quote grounding rate | 1.0000 |
| RAG context node seen rate | 1.0000 |
| Pipeline symptom precision | 1.0000 |
| Pipeline symptom recall | 0.9279 |
| Pipeline symptom F1 | 0.9626 |
| Negative false-positive rate | 0.0000 |

runtime fix 이전의 pipeline inspection 결과는 다음과 같았습니다.

| 항목 | 이전 값 |
| --- | ---: |
| Precision | 0.9091 |
| Recall | 0.7207 |
| F1 | 0.8040 |
| Negative false-positive rate | 0.1364 |

## What Changed

핵심 병목은 candidate availability가 아니었습니다. Track A combined IR은 이미 recall@5 = 1.0이었고, Track C에서 Bedrock extraction과 linking 이후 일부 증상이 손실되었습니다. 개선은 이 간극을 줄이는 데 집중했습니다.

주요 변경점:

1. span 내부 evidence가 있는 경우 broad source-text alias보다 `slot_ref`를 먼저 신뢰합니다.
2. LLM `slot_ref`가 틀렸지만 span name이 다른 canonical symptom과 직접 맞으면 직접 증상명이 override할 수 있습니다.
3. broad source quote를 domain quote pattern으로 좁힌 뒤 IR query를 구성합니다.
4. active `context` span도 name/slot이 ontology symptom에 매핑되면 rescue할 수 있습니다.
5. nasal obstruction guard를 추가해 코막힘 표현이 인후통 등 broad candidate로 흐르지 않도록 했습니다.
6. agenda-only anxiety와 nonspecific GI overread는 IR 전에 필터링합니다.
7. 고신호 패턴에 한해 co-occurring symptom rescue를 제한적으로 허용합니다.
8. duplicate matched slot은 canonical slot 기준으로 하나만 남깁니다.

## Final Remaining Mismatches

최종 run에서 남은 mismatch는 8건이며 모두 false negative입니다. false positive는 없습니다.

남은 8건은 모두 `progress_improved` 또는 `status=없음` 계열입니다.

| case_id | 해석 |
| --- | --- |
| `train_v2_055` | 인후통은 조금 나아졌지만 여전히 힘들 때가 있는 맥락 |
| `train_v2_056` | 가슴 답답함이 완화된 맥락 |
| `train_v2_064` | 열이 나아진 것 같다는 맥락 |
| `train_v2_065` | 심한 증상이 줄어든 맥락 |
| `train_v2_066` | 근육통이 조금 나아진 맥락 |
| `train_v2_068` | 기운 없음이 조금 나아진 맥락 |
| `train_v2_070` | 피로감은 완화됐지만 근육통은 현재 남은 mixed context |
| `train_v2_076` | 목소리 변화가 조금 나아진 맥락 |

## Clinical Policy Interpretation

현재 제품 정책은 `progress_improved`와 `symptom_absent`를 active symptom card 또는 IR `matched_slots`로 올리지 않습니다. 이 정보는 환자가 말한 맥락으로 보존되어야 하지만, 의료진 화면 최상단의 "오늘의 활성 증상"처럼 표시되면 오히려 위험할 수 있습니다.

따라서 남은 recall 손실은 후보 검색 실패나 IR linking 실패로 보기 어렵습니다. 더 타당한 해석은 다음과 같습니다.

```text
평가셋의 gold label은 개선/해소 계열 증상도 회수 대상으로 보았지만,
제품의 active symptom 정책은 해당 증상을 matched_slots에서 제외한다.
즉 남은 8건은 scoring-policy mismatch에 가깝다.
```

## Track-Level Interpretation

| Track | 해석 |
| --- | --- |
| Track A | offline candidate-search test. Bedrock을 호출하지 않으며 최종 모델 F1이 아님 |
| Track B | Gangwon dialect RAG layer가 anchor 행에서 검색되는지 확인 |
| Track C | S3/DynamoDB persistence를 monkeypatch한 실제 Bedrock pipeline test |

## Next Reporting Rule

이 결과를 최종 held-out performance로 보고하지 않습니다. 공개 가능한 첫 모델 성능은 locked `test_1000_v2`가 생성되고 freeze된 뒤 첫 실행 리포트에서 산출해야 합니다.

held-out report에서는 지표를 다음처럼 분리해야 합니다.

- active symptom F1: `matched_slots` only
- follow-up context coverage: `progress_improved` and `symptom_absent`
- negative symptom false-positive rate

이 분리가 있어야 recall 손실이 실제 누락인지, 제품 정책상 active card에서 제외한 것인지 설명할 수 있습니다.
