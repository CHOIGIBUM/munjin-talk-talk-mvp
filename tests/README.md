# 테스트 브랜치 안내

이 폴더는 문진톡톡의 추가 테스트 자료를 모읍니다. 일반 로컬 테스트는 기존 백엔드/프론트 위치에 있고, 이 폴더에는 실제 AWS 배포 환경을 점검하는 수동 통합 테스트를 둡니다.

```text
tests/
└── aws/
    ├── README.md
    └── test_aws_full.py
```

## 테스트 계층

| 계층 | 위치 | 실행 방식 | 외부 리소스 |
| --- | --- | --- | --- |
| 백엔드 단위/회귀 테스트 | `backend/serverless/tests/` | `pytest` | 기본적으로 없음 |
| 프론트엔드 단위 테스트 | `frontend/src/**/*.test.js` | `npm test` | 없음 |
| AWS 수동 통합 테스트 | `tests/aws/` | 직접 실행 또는 명시 플래그 pytest | Bedrock, DynamoDB, S3, Lambda |
| IR 평가 보조 코드 | `evaluation/ir/` | 평가 스크립트 직접 실행 | Titan/Bedrock 사용 가능 |

## 백엔드 로컬 테스트

백엔드 테스트는 스키마, 개인정보 마스킹, 질문셋, IR query/scoring, 사투리 RAG, orchestration, prompt golden fixture 등을 확인합니다.

```powershell
cd backend\serverless
pytest tests
```

상위 루트에서 실행할 경우 Python path와 의존성 상태에 따라 별도 설정이 필요할 수 있으므로, 기본 안내는 `backend/serverless` 기준입니다.

## 프론트엔드 로컬 테스트

프론트엔드는 Vitest를 사용합니다.

```powershell
cd frontend
npm test
```

현재 테스트 파일은 API client와 onepager adapter, 안전 키워드 설정 등 순수 로직 중심입니다.

## AWS 수동 통합 테스트

AWS 통합 테스트는 일반 로컬 테스트와 분리해서 봅니다.

```powershell
python tests\aws\test_aws_full.py
```

pytest로 실행하려면 명시적으로 플래그를 켭니다.

```powershell
$env:MUNJIN_RUN_AWS_INTEGRATION = "1"
pytest tests\aws\test_aws_full.py -s
```

환경변수와 실행 전 확인 사항은 [AWS 통합 테스트 README](aws/README.md)를 참고합니다.

## 관리 원칙

- AWS 리소스 식별자, 접근 코드, 토큰, 버킷명은 커밋하지 않습니다.
- 실제 환자 정보나 민감정보를 fixture에 넣지 않습니다.
- AWS 통합 테스트 실패를 단위 테스트 실패와 섞어 해석하지 않습니다.
- 비용이 발생하는 테스트는 CI 기본 경로에 넣지 않습니다.
- 평가 데이터와 Bedrock raw trace는 공개 저장소에 올리지 않습니다.
