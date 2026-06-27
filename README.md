# 문진톡톡 테스트 커버리지 브랜치

이 브랜치는 문진톡톡 공식 서비스 코드가 아니라, 로컬 단위 테스트와 실제 AWS 배포 환경 점검용 수동 통합 테스트를 정리한 테스트 브랜치입니다.

공식 서비스 설명과 실행 코드는 [main 브랜치](https://github.com/X-AI-KNU/munjin-talk-talk/tree/main)를 기준으로 봅니다. 이 브랜치는 해커톤 제출 시 "검증 체계와 AWS 통합 점검 방법"을 별도로 보여주기 위해 분리했습니다.

## 테스트 목적

문진톡톡은 프론트엔드, 서버리스 백엔드, Bedrock, DynamoDB, S3, Lambda, API Gateway가 함께 동작합니다. 이 브랜치는 모든 테스트를 한 종류로 섞지 않고 다음처럼 나눠 봅니다.

| 구분 | 위치 | 기본 실행 성격 |
| --- | --- | --- |
| 백엔드 단위/회귀 테스트 | `backend/serverless/tests/` | 로컬에서 pytest로 실행 |
| 프론트엔드 단위 테스트 | `frontend/src/**/*.test.js` | 로컬에서 Vitest로 실행 |
| AWS 수동 통합 테스트 | `tests/aws/test_aws_full.py` | 실제 AWS 리소스를 호출하므로 명시적으로만 실행 |
| IR 평가 보조 코드 | `evaluation/ir/` | 표준 증상 후보 검색/Linker 성능 점검 |

## 바로 보기

| 문서/파일 | 내용 |
| --- | --- |
| [테스트 브랜치 안내](tests/README.md) | 로컬 테스트와 AWS 통합 테스트의 구분 |
| [AWS 통합 테스트 설명](tests/aws/README.md) | 환경변수, 실행 전 체크리스트, 테스트 그룹 |
| [AWS 통합 테스트 스크립트](tests/aws/test_aws_full.py) | Bedrock, DynamoDB, S3, Lambda 직접 호출 |
| [IR 평가 안내](evaluation/ir/README.md) | 표준 증상 후보 검색과 Linker 평가 방법 |

## AWS 통합 테스트 범위

`tests/aws/test_aws_full.py`는 다음 항목을 확인합니다.

- Bedrock Nova Lite / Nova Pro 호출
- Titan Text Embedding v2 호출
- DynamoDB 세션 조회와 PII 미저장 구조 확인
- S3 artifact 버킷 접근과 onepaper/answers artifact 구조 확인
- Lambda 라우팅, 인증 실패, 입력 검증
- 기존 세션을 이용한 전체 파이프라인 E2E
- 증상 추출 프롬프트와 사투리 표준어 변환 품질
- 잘못된 접근 코드와 세션 토큰 접근 제어

## 실행 기준

일반 로컬 테스트는 비용 영향이 없고 반복 실행해도 됩니다. 반면 AWS 통합 테스트는 실제 Bedrock, DynamoDB, S3, Lambda를 호출하므로 배포 환경, 권한, 비용 영향을 확인한 뒤 수동으로 실행해야 합니다.

pytest 전체 실행에서 `tests/aws/test_aws_full.py`가 실수로 돌지 않도록, 이 파일은 `MUNJIN_RUN_AWS_INTEGRATION=1`이 설정된 경우에만 pytest에서 실행됩니다.

## 제출 시 해석 기준

다음처럼 표현하는 것은 적절합니다.

- 로컬 단위 테스트와 AWS 수동 통합 테스트를 분리해 관리했다.
- AWS 통합 테스트는 실제 배포 리소스 연결 상태를 확인하기 위한 수동 점검 스크립트다.
- 공개 저장소에는 Lambda 이름, API URL, 버킷명 같은 리소스 식별자를 커밋하지 않는다.

다음처럼 표현하면 안 됩니다.

- AWS 통합 테스트를 일반 CI에서 항상 자동 실행한다고 주장
- 통합 테스트 통과를 임상 성능 검증으로 해석
- 실제 계정/버킷/API 식별자를 README나 코드에 고정값으로 공개

이 브랜치는 "운영 배포가 항상 안전하다"는 보장이 아니라, 어떤 계층을 어떻게 검증할 수 있는지 정리한 테스트 근거입니다.
