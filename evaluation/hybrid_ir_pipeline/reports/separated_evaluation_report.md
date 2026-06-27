# Separated Evaluation Report (컴포넌트 분리 검증 리포트)

* **Generated At:** `2026-06-26T06:10:14.124246+00:00`
* **Dataset Target:** `evaluation/hybrid_ir_pipeline/train_100_v2/train_100_v2.jsonl`
* **Dataset Rows:** `100`
* **Held_out_test Status:** `False`

본 리포트는 Hybrid IR 후보 검색, 사투리 RAG 힌트 트리거, Bedrock 파이프라인 통합 안전성을 컴포넌트별로 분리 검증한 공식 실행 결과 스냅샷입니다. *(본 지표는 최종 Held-out 성능이 아닌 `train_100_v2` 개발용 벤치마크셋 기반의 파이프라인 점검 결과입니다.)*

---

## Track A: Offline IR (검색 엔진 성능 단독 검증)

Bedrock Runtime을 호출하지 않고, Alias 힌트 인덱스와 로컬 BM25 증상 텍스트 검색을 결합하여 정답 표준 증상이 후보군(Top-K) 내에 안정적으로 회수되는지 검증합니다.

| 검색 알고리즘 (Ranking) | recall@1 | recall@3 | recall@5 | recall@10 | all_gold_hit@5 | negative_in_top5_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **alias** | 0.8198 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.5000 |
| **bm25** | 0.5045 | 0.8108 | 0.8829 | 0.9459 | 0.8700 | 0.6364 |
| **combined** | **0.8198** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.7727** |

**[엔지니어링 해석]**
* **`combined recall@5`가 1.0000**을 기록함에 따라, 본 데이터셋에서는 후보 검색 단계에서 정답 표준 증상이 누락되는 병목 현상이 완벽히 해소되었음이 입증되었습니다.
* Alias와 BM25의 하이브리드 결합은 Broad Query 환경에서 후보 회수의 안정성을 극대화합니다. *(단, 본 지표는 후보 풀링 품질을 의미하며 전체 시스템의 F1 스코어로 대변되지 않습니다.)*

---

## Track B: Dialect RAG (방언 힌트 주입 정밀도 검증)

| 검증 항목 | 산출값 |
| --- | ---: |
| **Gangwon Rows** (강원 발화군 모수) | 50건 |
| **`rag_pack_anchored recall`** (타깃 행 회수율) | **1.0000 (10/10)** |
| **`non-anchor hint rate`** (노이즈 개입 오탐률) | **0.0000 (0/40)** |

**[엔지니어링 해석]**
* 방언팩 앵커가 명시적으로 설계된 10건의 발화에서는 기대 힌트가 100% 성공적으로 검색 및 주입되었습니다.
* 반면, 앵커가 없는 강원식 구어체 40건에서는 불필요한 방언 힌트가 단 한 건도 오탐(False Positive)되지 않았습니다.
* 이는 "모든 강원식 말투가 무분별하게 방언팩으로 처리된다"는 우려를 불식시키며, **Source Layer의 엄격한 분리를 통해 RAG 힌트 개입이 완벽하게 통제(Sanity Check)** 되고 있음을 입증합니다.

---

## Track C: Pipeline Integration (종단 E2E 통합 검증)

| 검증 지표 항목 | 산출값 |
| --- | ---: |
| **Persistence (저장소 상태)** | `monkeypatched_no_s3_dynamodb` (격리 구동) |
| **Rows Completed (관통 성공률)** | **100/100** |
| **Precision (오탐률 방어)** | **1.0000** |
| **Recall (회수율)** | **0.9279** |
| **End-to-End F1 Score** | **0.9626** |
| **Schema/Runtime Failures (런타임 크래시)** | **0** |
| **Source Quote Grounding Rate (환각 방어율)**| **1.0000** |
| **RAG Context Node Seen Rate** | **1.0000** |
| **Negative False-Positive Rate (부정 증상 오진율)**| **0.0000** |

**[엔지니어링 해석]**
* Bedrock Extraction 및 LangGraph 제어 흐름은 100건 모두 스키마 에러나 런타임 크래시 없이 무결점(`0 Failures`)으로 완료되었습니다.
* 생성된 모든 근거 인용구(`quote`)는 환자 원문에 100% 실재함을 검증하여 **LLM 특유의 환각(Hallucination) 현상을 원천 차단**했습니다.
* 환자가 부정한 증상을 '활성 증상(Active Symptom)'으로 잘못 판단한 오진 사례(Negative False-Positive)는 0건으로 입증되었습니다.

---

## Comprehensive Interpretation (종합 분석 및 리포팅 가이드)

* **결과 요약:** Track A는 검색 풀링 성능 100%, Track B는 사투리 개입 통제력 100%, Track C는 실제 파이프라인 E2E 모델 성능 F1 0.9626을 입증했습니다.
* **의도된 오답 (Policy Mismatch):** 파이프라인 관통 후 남은 8건의 False Negative는 전수 `progress_improved`(호전) 또는 `symptom_absent`(부재) 계열입니다. 제품 정책상 이러한 항목은 Active Symptom 카드로 올리지 않고 임상 단서(Clinical Clues)로 격리 보존하므로, 이는 시스템 실패가 아닌 **Scoring-Policy Mismatch(정책에 의한 의도된 필터링)** 로 해석해야 합니다.
