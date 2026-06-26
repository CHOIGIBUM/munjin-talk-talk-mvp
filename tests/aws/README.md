# AWS 통합 테스트

`test_aws_full.py`는 실제 AWS 리소스(Bedrock, DynamoDB, S3, Lambda)를 호출해 배포 환경 전체가 연결되어 있는지 확인하는 수동 통합 테스트입니다.

## 실행 전 환경변수

```powershell
$env:MUNJIN_REGION = "ap-northeast-2"
$env:MUNJIN_LAMBDA_NAME = "<lambda-function-name>"
$env:MUNJIN_API_URL = "https://<api-id>.execute-api.<region>.amazonaws.com"
$env:MUNJIN_TABLE = "MunjinSessions"
$env:MUNJIN_ARTIFACTS_BUCKET = "<artifacts-bucket-name>"
```

## 직접 실행

```powershell
python tests\aws\test_aws_full.py
```

## pytest로 실행

일반 `pytest` 전체 실행에서 실수로 AWS를 호출하지 않도록 기본값은 skip입니다. 이 파일만 pytest로 실행하려면 명시적으로 플래그를 켭니다.

```powershell
$env:MUNJIN_RUN_AWS_INTEGRATION = "1"
pytest tests\aws\test_aws_full.py -s
```

## 주의

이 테스트는 실제 Bedrock 호출과 AWS 리소스 접근을 수행하므로 권한, 배포 상태, 비용 영향을 확인한 뒤 실행해야 합니다. 공개 저장소에는 Lambda 이름, API URL, 버킷명 같은 리소스 식별자를 커밋하지 않습니다.
