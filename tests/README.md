# 테스트 브랜치 안내

이 브랜치는 기존 백엔드/프론트 단위 테스트에 더해 실제 AWS 배포 환경을 점검하는 수동 통합 테스트를 정리합니다.

```text
tests/
└── aws/
    ├── README.md
    └── test_aws_full.py
```

일반 로컬 테스트는 기존 위치를 사용합니다.

- 백엔드: `backend/serverless/tests/`
- 프론트엔드: `frontend/src/**/*.test.js`
- AWS 통합 테스트: `tests/aws/`
