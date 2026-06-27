# 런타임 데이터 배치 안내

이 폴더는 문진톡톡 백엔드가 질문셋, 방언 RAG, 표준 증상 IR, 도메인팩, few-shot을 수행할 때 참조하는 런타임 데이터 위치입니다.

`eval/hybrid-ir-pipeline` 브랜치에서는 이 폴더가 특히 중요합니다. Hybrid IR 평가가 단순 스크립트 점검이 아니라, 실제 운영 파이프라인이 읽는 domain pack, few-shot, symptom ontology와 어떻게 연결되는지를 보여주기 때문입니다.

## 현재 런타임 산출물 상태

오염 가능성이 있는 1차 런타임 학습/보강 데이터는 제거했고, 현재 포함된 도메인팩은 `symptom_index.json`의 87개 증상 ontology를 기본 슬롯으로 사용합니다.

`evaluation/hybrid_ir_pipeline/train_100_v2`의 승인된 100개 train 문장은 alias, quote pattern, few-shot 보강에만 사용합니다. 이 데이터는 held-out test가 아니라 train/inspection set입니다.

현재 재생성된 항목:

| 항목 | 설명 |
| --- | --- |
| `domain_packs/respiratory.json` | 87개 symptom rule, alias, safety flag, status enum, quote pattern |
| `fewshots/respiratory/*.json` | stage별 few-shot 예시 |
| `question_sets/default.json` | 초진/재진 Q1~Q4 질문 구조 |
| `dialect_packs/dialect_kangwon.json` | 강원 방언 RAG 힌트 참조 데이터 |
| `dialect_packs/dialect_kangwon.csv` | 방언팩 원본 관리용 표 데이터 |

`domain_packs/respiratory_fewshot.txt` 형식은 더 이상 주된 형식으로 사용하지 않고, stage별 JSON few-shot을 기준으로 봅니다.

## Hybrid IR 평가와의 관계

이 브랜치의 평가 흐름에서 런타임 데이터는 다음처럼 쓰입니다.

```text
train_100_v2 문장
  -> build_artifacts.py가 alias, quote pattern, few-shot 후보 생성
  -> domain_packs/respiratory.json에 반영
  -> run_separated_evaluation.py의 Track A/B/C에서 실제 후보 검색과 파이프라인 점검
```

중요한 기준은 `symptom_index.json`의 표준 증상 ontology를 기본 source로 둔다는 점입니다. `train_100_v2`는 ontology를 대체하지 않고, alias와 few-shot 보조 근거로만 사용합니다.

## 공개 저장소에 포함하지 않는 파일

| 파일 | 용도 | 제외 이유 |
| --- | --- | --- |
| `diseases_cleaned.json` | 질환 백과 원천 정리본 | 원천 본문과 파생 데이터의 공개 범위 검토 필요 |
| `symptom_index.json` | 표준 증상명과 질환 문서 연결 인덱스 | 원천 데이터 기반 파생 인덱스 |
| `symptom_embeddings_amazon.titan-embed-text-v2_0_512.json` | Titan embedding cache | 원천 증상 문서 기반 파생 벡터 |

이 세 파일이 없으면 공개 저장소 clone만으로 코드 구조 검토와 일부 테스트는 가능해도, 운영 수준의 Hybrid IR 표준 증상 매칭은 제한됩니다.

## 재구축 원칙

1. `evaluation/hybrid_ir_pipeline/design/`에서 생성/평가 설계를 먼저 확정합니다.
2. `blueprint/`에서 100개 row-level 조건을 고정합니다.
3. `train_100_v2/`에서 synthetic 환자 발화를 렌더링합니다.
4. `symptom_index.json`의 표준 증상 ontology를 기본 slot catalog로 둡니다.
5. `train_100_v2`만 보고 alias, quote pattern, few-shot 후보를 만듭니다.
6. 후보에는 근거 case id와 acceptance reason을 남깁니다.
7. 별도 locked test set을 만들기 전까지 train 결과를 held-out 성능으로 말하지 않습니다.

## 제출 시 해석 기준

이 폴더는 "데이터를 많이 넣었다"는 설명보다 "무엇을 공개하고 무엇을 공개하지 않았는지", "train-derived 보강과 ontology source를 어떻게 분리했는지"를 보여주는 문서입니다.

발표나 제출에서는 다음처럼 설명하는 것이 안전합니다.

```text
공개 저장소에는 실행 구조와 공개 가능한 도메인팩/few-shot만 포함했고,
원천 의료 백과 데이터와 파생 embedding cache는 공개하지 않았다.
Hybrid IR 평가는 표준 증상 ontology를 기준으로 alias와 few-shot 보강이
어떻게 후보 검색과 Bedrock linking에 영향을 주는지 분리해 확인했다.
```
