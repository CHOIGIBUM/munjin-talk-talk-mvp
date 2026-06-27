# 평가 브랜치 안내

이 폴더는 `eval/hybrid-ir-pipeline` 브랜치의 평가 자료 진입점입니다. 공식 서비스 설명은 루트 README와 `main` 브랜치를 기준으로 보고, 이 폴더에서는 Hybrid IR과 Bedrock 파이프라인을 어떻게 분리 평가했는지 확인합니다.

## 바로 보기

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

| 위치 | 역할 |
| --- | --- |
| `hybrid_ir_pipeline/README.md` | 평가팩 전체 설명, Track A/B/C 지표, 실행 방법 |
| `hybrid_ir_pipeline/design/` | 오염된 1차 평가를 걷어낸 뒤의 재설계 원칙 |
| `hybrid_ir_pipeline/blueprint/` | `train_100_v2` 생성을 위한 row-level 설계 |
| `hybrid_ir_pipeline/train_100_v2/` | 렌더링된 100개 synthetic 문진 발화와 런타임 산출물 builder |
| `hybrid_ir_pipeline/reports/` | 제출용 요약 지표와 오류 분석 |

## 평가 흐름

이 브랜치의 핵심은 성능을 한 숫자로 뭉뚱그리지 않는 것입니다.

```text
blueprint
  -> train_100_v2 렌더링
  -> runtime artifact 후보 생성
  -> Track A: Offline IR 후보 검색 점검
  -> Track B: Dialect RAG hint 검색 점검
  -> Track C: Bedrock/LangGraph 파이프라인 통합 점검
  -> reports 요약
```

## 제출 시 해석 기준

현재 결과는 `train_100_v2` 기반 점검 결과입니다. 최종 held-out 성능으로 말하면 안 됩니다. 발표나 제출에서는 아래처럼 표현하는 것이 안전합니다.

```text
Hybrid IR 브랜치에서는 후보 검색, 사투리 RAG 힌트, Bedrock 기반 파이프라인을 분리 평가했다.
현재 공개된 수치는 train_100_v2 점검 결과이며,
최종 일반화 성능은 별도 고정 테스트셋에서 첫 실행 리포트를 저장한 뒤 판단해야 한다.
```

## Git 관리 기준

- 평가 설계, 요약 리포트, 오류 분석은 커밋합니다.
- 실행별 raw output, Bedrock raw response trace, 비공개 원천 의료 데이터는 커밋하지 않습니다.
- held-out test 결과를 본 뒤 prompt나 alias를 고친 경우, 첫 실행 리포트와 튜닝 후 리포트를 섞지 않습니다.
