# 문진톡톡 문서 모음

이 폴더는 문진톡톡의 기술 구조, 데이터 흐름, 배포 방법, 보안 설계를 설명하는 문서 모음입니다.
평가자는 서비스가 어떤 문제를 어떤 구조로 해결하는지 확인할 수 있고, 개발자는 실제 배포와 유지보수에 필요한 기준을 확인할 수 있습니다.

---

## 평가자 추천 읽기 순서

| 순서 | 문서 | 확인할 내용 |
| --- | --- | --- |
| 1 | [루트 README](../README.md) | 문제 정의, 서비스 흐름, 핵심 기술, 보안 수준 |
| 2 | [평가 패키지](../evaluation/README.md) | main 브랜치의 공식 성능 요약과 공개/비공개 산출물 기준 |
| 3 | [LangGraph 문진 처리 파이프라인](LANGGRAPH_PIPELINE.md) | 환자 답변이 원페이퍼와 안내문으로 바뀌는 과정 |
| 4 | [내부 JSON 스키마](DATA_SCHEMA.md) | DynamoDB, S3 artifact, 원페이퍼, 안내문 데이터 구조 |
| 5 | [보안 데이터 인벤토리](SECURITY_DATA_INVENTORY.md) | 개인정보와 건강정보가 어디에 저장되고 어떻게 보호되는지 |
| 6 | [프로젝트 구조](PROJECT_STRUCTURE.md) | 프론트엔드와 백엔드 코드가 어떤 책임으로 나뉘어 있는지 |

---

## 개발자 추천 읽기 순서

| 순서 | 문서 | 확인할 내용 |
| --- | --- | --- |
| 1 | [프론트엔드 README](../frontend/README.md) | 화면 구성, 음성 문진 UX, API 호출 방식 |
| 2 | [백엔드 README](../backend/README.md) | 서버 측 책임, 비동기 분석, Hybrid IR, 저장 정책 |
| 3 | [Serverless Backend README](../backend/serverless/README.md) | API 목록, SAM 배포, 환경 변수, 런타임 데이터 |
| 4 | [런타임 데이터 배치 안내](../backend/serverless/src/data/README.md) | 공개 저장소에 없는 IR 데이터의 배치 기준 |
| 5 | [AWS 배포 가이드](DEPLOYMENT.md) | Amplify, API Gateway, Lambda, DynamoDB, S3 설정 |

---

## 문서 목록

| 파일 | 역할 |
| --- | --- |
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | 세션, 답변, 원페이퍼, 안내문, trace JSON 구조 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | AWS 배포 절차와 운영 설정 |
| [LANGGRAPH_PIPELINE.md](LANGGRAPH_PIPELINE.md) | LangChain/LangGraph 기반 문진 분석 파이프라인 |
| [MVP_SETUP.md](MVP_SETUP.md) | 로컬 실행, AWS 연결, 시연 전 점검 방법 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 저장소 폴더 구조와 주요 파일 책임 |
| [SECURITY_DATA_INVENTORY.md](SECURITY_DATA_INVENTORY.md) | 저장소별 데이터 경계, 가명처리, 보관 정책 |

---

## 평가와 검증 자료

`main` 브랜치에는 공식 서비스 설명과 핵심 성능 요약을 둡니다. 세부 실험과 테스트 근거는 아래 브랜치로 분리했습니다.

| 자료 | 역할 |
| --- | --- |
| [main/evaluation](../evaluation/README.md) | 공식 End-to-End 성능 평가 구조와 공개 요약 |
| [eval/dialect-rag](https://github.com/X-AI-KNU/munjin-talk-talk/tree/eval/dialect-rag) | 사투리 RAG 의미 보존 평가 |
| [eval/hybrid-ir-pipeline](https://github.com/X-AI-KNU/munjin-talk-talk/tree/eval/hybrid-ir-pipeline) | Hybrid IR 후보 검색과 Bedrock 파이프라인 분리 평가 |
| [test/add-coverage](https://github.com/X-AI-KNU/munjin-talk-talk/tree/test/add-coverage) | 로컬 테스트와 AWS 수동 통합 테스트 정리 |

심사위원이 성능 수치의 근거를 볼 때는 먼저 `main/evaluation`의 공식 요약을 보고, 사투리 RAG와 Hybrid IR의 세부 실험은 각 평가 브랜치에서 확인하면 됩니다.

---

## 현재 구현 기준

문진톡톡의 환자 화면은 Q1~Q4 답변을 모두 받은 뒤 `/process-answers`로 한 번에 저장합니다.
저장이 끝나면 환자는 바로 완료 화면으로 이동하고, 백그라운드 Lambda가 LangGraph 분석을 수행합니다. 환자가 문항마다 LLM 분석을 기다리는 구조가 아닙니다.

분석 파이프라인은 다음 기준으로 동작합니다.

- 음성 원본 파일은 저장하지 않고 Transcribe Streaming으로 텍스트만 받습니다.
- DynamoDB에는 세션 상태와 S3 artifact pointer 중심의 최소 정보만 저장합니다.
- 문진 답변, 원페이퍼, 환자 안내문, 최소 trace는 가명처리 후 S3에 저장합니다.
- LLM 출력은 Pydantic schema와 source quote 검증을 통과해야 운영 산출물에 반영됩니다.
- 증상 매칭은 LLM이 생성한 표현을 그대로 쓰지 않고, 원천 증상 데이터 기반 Hybrid IR과 linker 검증을 거칩니다.
- 운영 UI에는 임의 confidence나 내부 점수를 노출하지 않고 “매칭됨”, “우선 확인”처럼 의료진이 해석 가능한 상태만 표시합니다.

`/process-answer`는 과거 단일 문항 처리 방식과 일부 회귀 검증을 위한 보조 API입니다. 일반 시연과 실제 환자 문진 흐름에서는 `/process-answers`를 기준으로 보면 됩니다.

---

## 공개 문서 작성 원칙

- 현재 코드와 배포 구조에 반영된 내용을 기준으로 작성합니다.
- 의료 데이터 설명은 저장 위치, 보관 기간, 접근 경로, 비공개 처리 기준을 함께 적습니다.
- AI 설명은 모델 이름보다 입력, 출력, 검증 방식, 실패 처리 경로를 먼저 설명합니다.
- 실제 환자 발화 원문, 비공개 원천 데이터, AWS access key, 접근 코드, 로컬 개인 경로는 문서에 넣지 않습니다.
