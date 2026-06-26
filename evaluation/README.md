# 문진톡톡 평가 패키지

이 폴더는 문진톡톡의 핵심 성능을 설명하고 재현하기 위한 평가 자료를 모아 둔 공간입니다.

문진톡톡의 평가는 단순히 "LLM이 맞췄는가"를 보는 방식이 아닙니다. 실제 제품 흐름처럼 환자 발화를 먼저 구조화하고, 원문 근거를 검증한 뒤, 서울아산병원 질병백과 기반 표준 증상 후보와 다시 매칭합니다. 그래서 평가는 크게 두 층으로 나누어 봅니다.

| 평가 층 | 확인하는 질문 | 의미 |
| --- | --- | --- |
| End-to-End 문진 파이프라인 | 환자 발화에서 실제로 증상을 잘 추출하고 표준 증상까지 연결했는가 | 제품 사용자가 체감하는 최종 성능 |
| Hybrid IR 후보 검색 | 정답 표준 증상이 top-k 후보 안에 들어오는가 | LLM 이후 검색/매칭 병목을 분리해서 확인 |

## 공개 폴더 구성

```text
evaluation/
├── README.md                         # 평가 구조와 해석 기준
├── requirements.txt                  # 평가 실행에 필요한 Python 패키지
├── datasets/
│   └── eval_cases.sample.jsonl       # 공개 가능한 샘플 평가 입력
├── scripts/
│   ├── run_eval_suite.py             # E2E span 생성 + IR 평가를 이어서 실행
│   ├── run_pipeline_eval.py          # 운영 파이프라인 기반 span/매칭 평가
│   ├── run_ir_eval.py                # IR 후보 검색 + linker 평가
│   └── embedding_providers.py        # Titan/local embedding provider
└── reports/
    └── performance_summary.md        # 해커톤 설명용 성능 요약
```

공개 저장소에는 평가 코드, 샘플 입력, 성능 요약만 둡니다. 실제 대량 평가 데이터, Bedrock raw response, prompt 전문, embedding cache, 실행 결과 CSV/JSON은 저장소에 올리지 않습니다.

## 평가 데이터 형식

평가 데이터에는 환자 발화와 정답 표준 증상명만 넣습니다. `normalized_text`, `symptom_hint`, IR query는 사람이 미리 쓰지 않고 실제 파이프라인이 생성합니다. 그래야 운영 중 발생하는 LLM 추출 오차와 IR 매칭 오차가 평가에 함께 반영됩니다.

```json
{
  "case_id": "eval_001",
  "visit_type": "초진",
  "dialect_type": "standard",
  "question_id": "Q1",
  "text": "어제부터 목이 칼칼하고 코가 막혀요.",
  "gold_symptoms": ["목의 통증", "코막힘"],
  "negative_symptoms": []
}
```

`gold_symptoms`와 `negative_symptoms`는 운영 `symptom_index.json`에 존재하는 표준 증상명이어야 합니다.

## 실행 방법

프로젝트 루트에서 의존성을 설치합니다.

```powershell
pip install -r evaluation\requirements.txt
```

샘플 데이터로 E2E span 생성과 IR 평가를 한 번에 실행합니다.

```powershell
python evaluation\scripts\run_eval_suite.py `
  --input evaluation\datasets\eval_cases.sample.jsonl `
  --output-dir evaluation\outputs\sample_run `
  --top-k 20
```

파이프라인 평가와 IR 평가를 따로 볼 수도 있습니다.

```powershell
python evaluation\scripts\run_pipeline_eval.py `
  --input evaluation\datasets\eval_cases.sample.jsonl `
  --output-dir evaluation\outputs\pipeline

python evaluation\scripts\run_ir_eval.py `
  --input evaluation\outputs\pipeline\pipeline_ir_eval_cases.jsonl `
  --output-dir evaluation\outputs\ir_g_rrf_top20 `
  --top-k 20
```

## 주요 지표

| 지표 | 해석 |
| --- | --- |
| `Precision` | 예측한 표준 증상 중 정답인 비율 |
| `Recall` | 정답 표준 증상 중 실제로 찾아낸 비율 |
| `F1` | Precision과 Recall의 균형 지표 |
| `candidate_recall@k` | IR top-k 후보 안에 정답 증상이 들어온 비율 |
| `negative_hit@k` | 부정/호전/무관 증상이 후보에 섞인 비율 |
| `exact_match_rate` | 케이스 단위로 정답 증상 집합이 완전히 일치한 비율 |

심사 자료에서는 End-to-End F1만 단독으로 말하지 않고, 후보 검색 성능과 함께 설명합니다. 그래야 "LLM이 틀린 것인지", "검색 후보가 부족한 것인지", "후보는 있었지만 최종 선택이 흔들린 것인지"를 구분할 수 있습니다.

## 해커톤 보고용 성능 요약

자세한 수치와 해석은 [reports/performance_summary.md](reports/performance_summary.md)에 정리했습니다.

요약하면, 일반 호흡기 문진 150개 focused benchmark에서는 End-to-End F1 0.8934를 기록했습니다. 이 평가는 문진톡톡이 목표로 한 일반 외래 호흡기 문진 상황에 가장 가까운 설명용 지표입니다. 반면, 중증 징후와 비호흡기 confounder까지 넓게 섞은 held-out 500개에서는 F1이 약 0.75 수준으로 낮아집니다. 따라서 문진톡톡은 "모든 임상 증상을 포괄하는 자동 진단기"가 아니라, "고령 환자의 호흡기 문진 발화를 의료진이 빠르게 확인할 수 있게 정리하는 보조 도구"로 설명하는 것이 정확합니다.

## Git 관리 기준

커밋하지 않는 항목:

```text
evaluation/datasets/eval_cases.jsonl
evaluation/outputs/
evaluation/cache/
evaluation/reports/generated/
```

대량 평가 데이터와 실행 산출물은 필요할 때 로컬 또는 별도 제출 자료에서 관리합니다.
