# Train 100 v2 렌더링 데이터

이 폴더는 `blueprint/case_blueprint.jsonl`에서 생성한 100개 synthetic 환자 발화와, 그 데이터를 이용해 런타임 후보 검색 보조 산출물을 만드는 스크립트를 담습니다.

이 데이터는 학습/점검용입니다. Held-out 성능으로 보고하면 안 됩니다.

## 데이터 성격

`train_100_v2.jsonl`은 실제 환자 데이터가 아니라 blueprint를 바탕으로 렌더링한 synthetic 문진 발화입니다. 목적은 운영 파이프라인을 바로 튜닝하기 전, 후보 검색과 Bedrock 추출이 어떤 유형에서 흔들리는지 확인하는 것입니다.

`quality_gate_report.json` 기준 100개 행은 초진 Q1 50개, 재진 Q3 50개이며, 표준어 50개와 강원체 50개로 나뉩니다. 강원체 50개 중 10개만 실제 방언 pack anchor를 의도적으로 포함한 `rag_pack_anchored` 행입니다.

## 파일

- `train_100_v2.jsonl`: 렌더링된 환자 발화 100개입니다.
- `quality_gate_report.json`: 렌더링 데이터 검증 요약입니다.
- `render_train.py`: Bedrock 기반 렌더링 스크립트입니다.
- `build_artifacts.py`: ontology와 `train_100_v2`를 이용해 domain pack/few-shot 후보를 만드는 스크립트입니다.
- `artifact_build_report.json`: 생성 산출물 개수와 분포 검증 요약입니다.

상세 provenance와 실행별 raw output은 커밋하지 않습니다.

## 런타임 산출물 생성

프로젝트 루트에서 실행합니다.

```powershell
python -X utf8 evaluation\hybrid_ir_pipeline\train_100_v2\build_artifacts.py
```

builder는 다음 파일을 갱신할 수 있습니다.

- `backend/serverless/src/data/domain_packs/respiratory.json`
- `backend/serverless/src/data/fewshots/respiratory/*.json`

`backend/serverless/src/data/symptom_index.json`을 제품 ontology source로 사용하고, `train_100_v2.jsonl`은 alias, quote-pattern, few-shot 후보 보조 자료로만 사용합니다.

## 산출물 요약

`artifact_build_report.json` 기준입니다.

| 항목 | 값 |
| --- | ---: |
| train rows | 100 |
| ontology symptoms | 87 |
| symptom rules | 87 |
| alias patterns | 142 |
| train-derived alias patterns | 55 |
| train alias full gold rows | 100 |
| provenance entries | 250 |
| test data used | false |

`test_data_used`가 `false`인 점이 중요합니다. 이 산출물은 train set 점검에서 만든 보조 자료이며, held-out test 결과를 보고 다시 맞춘 산출물이 아닙니다.

## 평가와의 관계

`train_100_v2`는 세 평가 트랙에 모두 연결됩니다.

| 트랙 | 이 데이터가 쓰이는 방식 |
| --- | --- |
| Track A: Offline IR | 환자 발화와 gold symptom으로 alias/BM25/combined 후보 검색 품질 확인 |
| Track B: Dialect RAG | `rag_pack_anchored` 행에서 기대 방언 힌트가 검색되는지 확인 |
| Track C: Pipeline Integration | Bedrock extraction과 Hybrid IR linking 후 최종 `matched_slots` 확인 |

따라서 이 폴더의 데이터는 평가 파이프라인의 중심 입력이지만, 최종 공개 성능을 주장하는 test set은 아닙니다.

## 제출 시 해석 기준

다음처럼 표현하는 것이 안전합니다.

```text
train_100_v2는 100개 synthetic 문진 발화로 구성된 파이프라인 점검용 데이터이며,
표준어/강원체, 초진/재진, 증상군, 상태 패턴을 고르게 포함하도록 설계했다.
이 데이터로 후보 검색과 Bedrock 파이프라인을 점검했지만,
최종 held-out 성능은 별도 고정 테스트셋에서 보고해야 한다.
```
