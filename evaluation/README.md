# 평가 디렉터리 안내

이 디렉터리는 `eval/hybrid-ir-pipeline` 브랜치에서 수행한 성능 검증 자료의 진입점입니다. 공식 서비스 설명, 배포 방법, 사용자 화면 흐름은 `main` 브랜치의 문서를 기준으로 보고, 이 브랜치의 `evaluation/` 문서는 Hybrid IR, 사투리 RAG, Bedrock 기반 구조화 파이프라인을 컴포넌트 단위로 어떻게 분리 검증했는지 설명합니다.

핵심 목적은 하나입니다.

```text
LLM이 만든 자유 텍스트 결과를 그대로 믿지 않고,
후보 검색(IR), 방언 힌트 검색, Bedrock 추출/검증/링킹을 분리해서
어느 구간이 안정적으로 작동하고 어느 구간을 보완해야 하는지 추적한다.
```

## 바로 보기

| 위치 | 역할 |
| --- | --- |
| [hybrid_ir_pipeline/README.md](hybrid_ir_pipeline/README.md) | Track A/B/C 평가 구조, 데이터셋, 지표, 실행 방법을 설명하는 평가팩 메인 문서 |
| [hybrid_ir_pipeline/reports/metrics_summary.json](hybrid_ir_pipeline/reports/metrics_summary.json) | 100건 `train_100_v2` 기준 요약 지표 스냅샷 |
| [hybrid_ir_pipeline/reports/separated_evaluation_report.md](hybrid_ir_pipeline/reports/separated_evaluation_report.md) | Track A/B/C 분리 평가 결과 리포트 |
| [hybrid_ir_pipeline/reports/pipeline_error_analysis.md](hybrid_ir_pipeline/reports/pipeline_error_analysis.md) | 남은 mismatch 8건의 원인과 임상 정책 해석 |
| [hybrid_ir_pipeline/design/README.md](hybrid_ir_pipeline/design/README.md) | 평가 재설계 배경, train/test 분리 원칙, 데이터 설계 기준 |
| [hybrid_ir_pipeline/design/evaluation_tracks.md](hybrid_ir_pipeline/design/evaluation_tracks.md) | Offline IR, Dialect RAG, Pipeline Integration, Product E2E 트랙 정의 |
| [hybrid_ir_pipeline/blueprint/README.md](hybrid_ir_pipeline/blueprint/README.md) | 100건 평가 데이터 생성 전 row-level 분포 설계 |
| [hybrid_ir_pipeline/train_100_v2/README.md](hybrid_ir_pipeline/train_100_v2/README.md) | 렌더링된 100건 synthetic 문진 데이터와 산출물 설명 |

## 폴더 구조

```text
evaluation/
└── hybrid_ir_pipeline/
    ├── README.md
    ├── run_separated_evaluation.py
    ├── blueprint/
    ├── design/
    ├── train_100_v2/
    └── reports/
```

## 평가 흐름

```text
blueprint 설계
  -> train_100_v2 문진 발화 렌더링
  -> 평가용 domain pack / few-shot 후보 산출
  -> Track A: Offline IR 후보 검색 평가
  -> Track B: Dialect RAG hint 검색 평가
  -> Track C: Bedrock/LangGraph 통합 파이프라인 평가
  -> reports 요약 및 mismatch 분석
```

## main 브랜치와의 경계

`main` 브랜치는 실제 서비스 코드와 공식 설명 문서의 기준입니다. 이 브랜치는 서비스 동작을 대체하지 않고, 다음 질문에 답하기 위해 남겨 둔 평가 근거입니다.

| 질문 | 이 브랜치에서 확인하는 문서 |
| --- | --- |
| 표준 증상 후보가 검색 단계에서 누락되지 않는가 | `Track A: Offline IR` |
| 사투리 힌트가 필요한 곳에서만 검색되는가 | `Track B: Dialect RAG Sanity` |
| Bedrock 추출과 IR 링킹을 거친 최종 결과가 안전한가 | `Track C: Pipeline Integration` |
| 남은 false negative가 시스템 오류인지 정책 차이인지 | `pipeline_error_analysis.md` |

## 제출 시 해석 기준

현재 공개된 수치는 `train_100_v2` 100건으로 수행한 파이프라인 점검 결과입니다. 해커톤 제출에서는 아래처럼 설명하는 것이 안전합니다.

```text
Hybrid IR 평가 브랜치에서는 후보 검색, 사투리 RAG 힌트, Bedrock 기반 추출/링킹 파이프라인을 분리 검증했다.
train_100_v2 평가에서 Offline IR combined recall@5는 1.0,
Pipeline Integration F1은 0.9626이었으며,
남은 mismatch는 active symptom 정책과 평가 라벨 기준의 차이로 분석했다.
```

반대로 아래처럼 표현하면 안 됩니다.

- `train_100_v2` 결과를 최종 held-out 성능이라고 표현
- Track A의 후보 검색 recall을 전체 모델 F1처럼 표현
- 남은 8건 false negative를 단순 오류로 단정
- 평가셋 결과를 본 뒤 prompt, alias, few-shot, domain pack을 고쳤다는 인상을 주는 서술

## Git 관리 기준

커밋해도 되는 항목:

- 평가 설계 문서
- blueprint와 train_100_v2 데이터
- quality gate report
- 요약 리포트와 오류 분석
- 평가 실행 스크립트

커밋하지 않는 항목:

- 실행별 raw Bedrock response trace
- 임시 output directory
- 비공개 원천 의료 데이터
- 실제 AWS 계정, 버킷, API URL, credential 정보
