# 문진톡톡 Hybrid IR 파이프라인 평가팩

이 폴더는 문진톡톡의 증상 후보 검색 엔진, 사투리 RAG 힌트 검색, Bedrock 기반 구조화 파이프라인을 분리해서 검증하기 위한 평가팩입니다. 공식 서비스 코드 브랜치가 아니라, 해커톤 심사와 기술 검토에서 "왜 이 파이프라인이 안전하게 설계되었는가"를 설명하기 위한 근거 자료입니다.

## 평가 목적

문진톡톡은 환자 발화를 LLM의 자유 생성 결과에 그대로 맡기지 않습니다. LLM은 환자 발화를 구조화하고, 표준 증상 연결은 Hybrid IR 후보 검색과 검증 단계를 거칩니다. 이 평가팩은 다음 세 질문을 분리해서 봅니다.

| 질문 | 평가 트랙 |
| --- | --- |
| 정답 표준 증상이 후보군 안에 안정적으로 들어오는가 | Track A: Offline IR |
| 강원 사투리 힌트가 필요한 행에서만 검색되는가 | Track B: Dialect RAG Sanity |
| Bedrock 추출, schema 검증, IR 링킹을 통과한 최종 `matched_slots`가 임상 정책에 맞는가 | Track C: Pipeline Integration |

이 분리는 중요합니다. 후보 검색이 완벽해도 LLM 추출이나 상태 정책에서 최종 결과가 달라질 수 있고, 반대로 최종 F1만 보면 후보 검색 단계의 병목을 찾기 어렵습니다.

## 파일 구성

```text
evaluation/hybrid_ir_pipeline/
├── README.md
├── run_separated_evaluation.py
├── blueprint/
│   ├── README.md
│   ├── case_blueprint.jsonl
│   ├── case_blueprint.schema.json
│   ├── distribution_plan.json
│   └── quality_gate_report.json
├── design/
│   ├── README.md
│   ├── evaluation_tracks.md
│   └── train_100_v2_blueprint_draft.md
├── train_100_v2/
│   ├── README.md
│   ├── train_100_v2.jsonl
│   ├── quality_gate_report.json
│   ├── artifact_build_report.json
│   ├── build_artifacts.py
│   └── render_train.py
└── reports/
    ├── metrics_summary.json
    ├── separated_evaluation_report.md
    └── pipeline_error_analysis.md
```

| 위치 | 역할 |
| --- | --- |
| `blueprint/` | 100건 평가 데이터가 특정 증상군이나 말투에 치우치지 않도록 분포를 먼저 고정 |
| `train_100_v2/` | blueprint를 바탕으로 렌더링한 synthetic 문진 발화와 평가용 산출물 builder |
| `design/` | 평가 재설계 원칙, train/test 분리 기준, 트랙별 측정 범위 |
| `reports/` | Track A/B/C 결과와 mismatch 해석 |
| `run_separated_evaluation.py` | 세 평가 트랙을 한 번에 실행하는 러너 |

## 데이터셋 개요

현재 평가는 `train_100_v2/train_100_v2.jsonl`의 100건 synthetic 문진 발화를 기준으로 합니다. 이 데이터는 운영 환자 데이터가 아니며, 파이프라인 점검과 개발용 평가를 위해 설계한 데이터입니다.

`blueprint/quality_gate_report.json`과 `train_100_v2/quality_gate_report.json` 기준 분포는 다음과 같습니다.

| 항목 | 분포 |
| --- | --- |
| 방문/질문 | 초진 Q1 50건, 재진 Q3 50건 |
| 언어 스타일 | 표준어 50건, 강원식 구어체 50건 |
| 방언 source layer | none 50건, clinical_colloquial 25건, rag_pack_anchored 10건, light_dialect_style 15건 |
| 증상군 | upper airway 18, cough/sputum/lower airway 20, dyspnea/chest/urgent 18, systemic course 14, ENT/swallow/eye/voice 10, cardio/neuro/edema 10, GI confounders 10 |
| 상태 패턴 | active_current 45, recurrent_or_persistent 25, improved_or_resolved 10, denied_negative_context 15, mixed_context 5 |

이 데이터셋은 개발/평가용입니다. 최종 held-out 성능은 별도 고정 테스트셋에서 첫 실행 리포트를 보관한 뒤에만 주장해야 합니다.

## 평가 트랙

### Track A: Offline IR

Bedrock을 호출하지 않습니다. 로컬 alias retrieval, BM25 symptom reference retrieval, combined candidate ranking만 실행합니다.

확인 질문:

- 정답 표준 증상이 top-k 후보 안에 들어오는가?
- alias와 BM25를 결합했을 때 후보 검색이 보완되는가?
- 후보 검색 단계에서 이미 정답이 빠지는 케이스가 있는가?

주요 지표:

- `recall@1`, `recall@3`, `recall@5`, `recall@10`
- `all_gold_hit@5`
- `negative_in_top5_rate`

주의: Track A는 후보 검색 품질입니다. 최종 모델 F1이나 onepaper 품질로 직접 해석하면 안 됩니다.

### Track B: Dialect RAG Sanity

Bedrock을 호출하지 않습니다. 강원 방언팩에 실제 anchor가 있는 `rag_pack_anchored` 행에서 기대한 힌트가 검색되는지 확인합니다.

확인 질문:

- 방언 pack anchor가 있는 10건에서 기대 힌트가 검색되는가?
- anchor가 없는 강원식 구어체 행에서 방언 힌트가 과하게 검색되지 않는가?

주요 지표:

- `rag_pack_anchored_recall`
- `non_anchor_hint_rate`

### Track C: Pipeline Integration

Bedrock을 호출합니다. 실제 `run_answer_pipeline` 계열 흐름을 사용하되, S3/DynamoDB 저장은 monkeypatch하여 평가 중 외부 저장소에 쓰지 않습니다.

확인 질문:

- Bedrock extraction이 schema-valid 결과를 내는가?
- RAG context node가 파이프라인 상태에 포함되는가?
- `source_quote`가 환자 원문 문자열에 실제로 존재하는가?
- Hybrid IR linking 이후 active symptom `matched_slots`가 기준 증상과 맞는가?
- 부정 증상이나 호전된 증상이 active symptom으로 잘못 올라가지 않는가?

주요 지표:

- micro precision, recall, F1
- schema/runtime failures
- source quote grounding rate
- RAG context node seen rate
- negative false-positive rate

## 현재 요약 지표

`reports/metrics_summary.json` 기준입니다.

| 지표 | 값 |
| --- | ---: |
| generated_at | `2026-06-26T06:10:14.124246+00:00` |
| dataset rows | 100 |
| held_out_test | false |
| Track A combined recall@1 | 0.8198 |
| Track A combined recall@3 | 1.0000 |
| Track A combined recall@5 | 1.0000 |
| Track A combined recall@10 | 1.0000 |
| Track A all_gold_hit@5 | 1.0000 |
| Track B rag-pack anchored recall | 1.0000 |
| Track B non-anchor hint rate | 0.0000 |
| Track C completed rows | 100/100 |
| Track C precision | 1.0000 |
| Track C recall | 0.9279 |
| Track C F1 | 0.9626 |
| Track C schema/runtime failures | 0 |
| Track C source quote grounding rate | 1.0000 |
| Track C RAG context node seen rate | 1.0000 |
| Track C negative false-positive rate | 0.0000 |

## 오류 분석 요약

`reports/pipeline_error_analysis.md` 기준으로 최종 mismatch는 8건이며 모두 false negative입니다. 공통 패턴은 `progress_improved` 또는 `status=없음` 계열입니다.

예시:

- `train_v2_055`: 인후통은 조금 나아졌지만 여전히 힘들 때가 있음
- `train_v2_064`: 열이 나아진 것 같음
- `train_v2_070`: 피로감은 완화됐지만 근육통은 현재 남음
- `train_v2_076`: 목소리 변화가 조금 나아짐

현재 제품 정책은 `progress_improved`와 `symptom_absent`를 active symptom card 또는 IR `matched_slots`로 올리지 않습니다. 이 항목들은 follow-up context 또는 clinical clue로 보존하는 쪽에 가깝습니다. 따라서 남은 recall 손실은 후보 검색 실패가 아니라 평가 라벨 기준과 제품 라우팅 정책의 차이로 해석해야 합니다.

## 실행 준비

프로젝트 루트에서 실행한다고 가정합니다.

```bash
cd munjin-talk-talk

export AWS_PROFILE=<your-profile>
export AWS_REGION=ap-northeast-2
export AWS_DEFAULT_REGION=ap-northeast-2
```

Windows PowerShell:

```powershell
$env:AWS_PROFILE="<your-profile>"
$env:AWS_REGION="ap-northeast-2"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
```

Track C는 Bedrock을 호출하므로 AWS 권한과 비용 영향이 있습니다. Track A/B만 보는 코드 경로는 Bedrock에 의존하지 않지만, 현재 통합 러너는 Track C까지 함께 실행하는 구조입니다.

## 평가 실행

```bash
python evaluation/hybrid_ir_pipeline/run_separated_evaluation.py \
  --dataset evaluation/hybrid_ir_pipeline/train_100_v2/train_100_v2.jsonl \
  --out-dir evaluation/hybrid_ir_pipeline/reports/run_latest
```

제출 또는 발표에는 아래 고정 결과 파일을 기준으로 사용합니다.

- `reports/metrics_summary.json`
- `reports/separated_evaluation_report.md`
- `reports/pipeline_error_analysis.md`

실행별 raw output, Bedrock raw response trace, 임시 디렉터리는 공개 저장소에 커밋하지 않습니다.

## Git 관리 기준

커밋 권장:

- 평가 설계 문서
- blueprint, train_100_v2 데이터셋, quality gate report
- 고정 요약 report와 error analysis
- 평가 실행 스크립트

커밋 금지:

- Bedrock raw response trace
- 실행별 임시 output directory
- S3/DynamoDB persistence 결과물
- held-out test 실패를 보고 뒤늦게 고친 prompt/alias/few-shot 산출물

## 해석 시 주의

현재 수치는 `train_100_v2` 기반 파이프라인 평가 결과입니다. 최종 모델 성능이나 held-out 성능으로 표현하면 안 됩니다.

발표나 제출에서는 다음처럼 말하는 것이 안전합니다.

```text
문진톡톡은 후보 검색, 사투리 RAG 힌트, Bedrock 기반 추출/연결 파이프라인을 분리 평가했다.
train_100_v2 평가에서 Offline IR combined recall@5는 1.0,
Pipeline Integration F1은 0.9626이었고,
남은 mismatch는 제품 정책상 active symptom으로 올리지 않는 개선/해소 계열에서 발생했다.
```

최종 공개 성능 주장은 별도 고정 테스트셋의 첫 실행 리포트를 보관한 뒤, 그 이후의 튜닝 기록과 분리해서 관리해야 합니다.
