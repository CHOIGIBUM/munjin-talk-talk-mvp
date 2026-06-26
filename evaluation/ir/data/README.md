# IR Evaluation Data

이 폴더는 문진톡톡 IR/파이프라인 평가에 사용할 데이터를 보관하는 위치입니다. 현재 브랜치에서는 과거 테스트에 사용했던 데이터와 원본 백업을 모두 제거했습니다.

## 현재 상태

| 경로 | 상태 |
| --- | --- |
| `generated/` | 새 v2 생성 데이터가 들어갈 자리만 유지 |
| `raw/` | 과거 원본 백업 제거 |
| legacy manual dev files | 제거 |

## 새 v2 데이터 위치

새 데이터는 아래 위치에 생성합니다.

| 경로 | 용도 |
| --- | --- |
| `generated/train_100/blueprint.json` | 100건 training set 설계 |
| `generated/train_100/cases.json` | alias/few-shot/domain 보강에 사용할 training set |
| `generated/train_100/manifest.json` | 생성 조건, 모델, seed, 검증 요약 |
| `generated/test_1000/blueprint.json` | 1000건 locked test 설계 |
| `generated/test_1000/cases.locked.json` | 최종 평가 전까지 개별 실패를 보지 않는 locked test set |
| `generated/test_1000/manifest.json` | 생성 조건, 모델, seed, 검증 요약, lock 여부 |

## 데이터 분리 규칙

- `train_100`은 열람과 실패 분석이 가능합니다.
- `train_100`에서 만든 alias/few-shot은 반드시 `evaluation/ir/derived/`에 근거를 남깁니다.
- `test_1000`은 성능 측정용입니다.
- `test_1000`의 개별 실패를 분석해서 코드를 바꾸면 새 test set을 다시 생성합니다.
- 표준어 50%, 강원도 사투리/구어체 50% 비율을 기본으로 합니다.
- 현재 증상 IR 평가는 초진 Q1, 재진 Q3를 우선 대상으로 합니다.

## 검증

```powershell
python evaluation\ir\validate_eval_data.py `
  --input evaluation\ir\data\generated\train_100\cases.json
```

```powershell
python evaluation\ir\validate_eval_data.py `
  --input evaluation\ir\data\generated\test_1000\cases.locked.json `
  --summary-output evaluation\ir\outputs\test_1000_validation_summary.json
```
