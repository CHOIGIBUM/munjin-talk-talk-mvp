# 평가 트랙 정의

Hybrid IR 재설계의 핵심은 retrieval, LLM extraction, product behavior를 하나의 점수로 섞지 않는 것입니다. 이 문서는 각 트랙이 무엇을 실행하고, 무엇을 실행하지 않으며, 어떤 지표로 해석해야 하는지 정리합니다.

## Track A: Offline IR

실행하는 것:

- local alias retrieval
- local symptom reference retrieval
- BM25 candidate ranking
- combined candidate ranking

실행하지 않는 것:

- Bedrock 호출
- LangGraph 전체 파이프라인
- S3 또는 DynamoDB write

목적:

- 정답 표준 증상이 후보 리스트에 들어오는지 확인합니다.
- LLM 비용을 쓰기 전에 candidate-search failure를 진단합니다.
- alias, BM25, combined ranking 중 어느 신호가 후보 검색을 보완하는지 봅니다.

주요 지표:

- recall@1, recall@3, recall@5, recall@10
- all-gold-hit@5
- negative-in-top5
- directness-stratified recall
- dialect-layer-stratified recall

해석:

Track A 점수는 "IR 후보 풀링이 좋은가"를 말합니다. 최종 onepaper 품질, 최종 Bedrock 추출 성능, 전체 제품 F1을 의미하지 않습니다.

## Track B: Dialect RAG Sanity

실행하는 것:

- current Gangwon dialect pack retrieval
- source-layer checking
- `rag_pack_anchored` 행의 기대 힌트 검색 여부 확인

실행하지 않는 것:

- 기본적으로 Bedrock 호출 없음
- 전체 문진 파이프라인 실행 없음

목적:

- `rag_pack_anchored`로 표시한 행이 실제 방언팩 근거를 갖는지 확인합니다.
- 강원식 말투 전체를 방언 RAG 성공 사례로 과장하지 않도록 막습니다.
- anchor가 없는 구어체 행에서 불필요한 RAG hint가 과하게 붙지 않는지 봅니다.

주요 지표:

- dialect hint recall@k for `rag_pack_anchored` rows
- false dialect hint rate for `clinical_colloquial`
- false dialect hint rate for `light_dialect_style`
- non-anchor hint rate

해석:

Track B는 방언 RAG의 "개입 타당성"을 봅니다. 방언팩이 실제로 커버하는 표현과 단순 지역 말투를 구분하는 것이 핵심입니다.

## Track C: Pipeline Integration

실행하는 것:

- `run_answer_pipeline` 또는 동기 파이프라인 실행
- dialect normalization
- RAG context retrieval
- Bedrock extraction
- schema validation
- hybrid IR linking

실행 방식:

- S3/DynamoDB persistence는 평가 중 monkeypatch합니다.
- Bedrock 호출은 실제로 발생할 수 있습니다.
- 환자 원문 기반 `source_quote` grounding을 확인합니다.

목적:

- 실제 추출/링킹 동작을 측정합니다.
- RAG context가 prompt/state에 포함되는지 확인합니다.
- Bedrock이 schema-valid이고 transcript-grounded output을 반환하는지 봅니다.
- active symptom policy가 부정/호전 증상을 잘못 올리지 않는지 확인합니다.

주요 지표:

- symptom micro precision, recall, F1
- symptom macro F1 by group
- status accuracy
- negative symptom false-positive rate
- source-quote grounding rate
- Bedrock/schema failure rate
- RAG context node seen rate

해석:

Track C가 현재 브랜치에서 실제 파이프라인 성능에 가장 가까운 지표입니다. 다만 `train_100_v2`는 개발용 데이터이므로 최종 held-out 성능으로 말하면 안 됩니다.

## Track D: Product E2E

실행하는 것:

- patient Q1-Q4 submit flow
- async Lambda analysis
- S3/DynamoDB persistence
- onepaper refresh
- staff and doctor UI readiness states

목적:

- 모델/파이프라인 평가가 충분히 안정된 뒤 실제 제품 흐름을 검증합니다.
- 환자 화면이 Bedrock 처리 때문에 막히지 않는지 확인합니다.
- 직원/의료진 화면이 같은 세션 상태를 일관되게 보는지 확인합니다.

주요 지표:

- session reaches expected status
- onepaper generated
- no patient-facing blocking on Bedrock
- staff/doctor views show consistent state
- consent/refusal/access-control flow works as expected

해석:

Track D는 성능 평가라기보다 제품 통합 검증입니다. 이 브랜치에서는 정의와 기준을 제공하고, 실제 운영 검증은 배포 환경과 테스트 브랜치 문서에서 관리합니다.

## Reporting Rule

절대 하지 말아야 할 표현:

- Track A IR recall을 최종 모델 F1이라고 설명
- `train_100_v2` 결과를 held-out 성능이라고 설명
- 방언 source layer 전체를 RAG pack 근거라고 설명
- negative symptom false-positive 방어를 빼고 recall만 강조

권장 표현:

```text
Track A는 후보 검색 품질, Track B는 사투리 RAG 힌트 타당성,
Track C는 Bedrock/LangGraph 통합 파이프라인 성능을 각각 분리해 측정한다.
최종 공개 성능은 locked held-out test set의 첫 실행 리포트에서 별도로 보고해야 한다.
```
