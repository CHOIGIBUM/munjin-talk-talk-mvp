"""S3 기반 문진 산출물 저장소.

DynamoDB는 대기열과 상태 조회용 최소 메타데이터만 보관하고, 환자 발화,
LLM 추출 결과, 원페이퍼, 환자 안내문처럼 큰 의료 문진 JSON은 이 모듈을
통해 S3에 저장합니다. 프론트엔드는 S3에 직접 접근하지 않고 Lambda API를
통해 필요한 산출물만 받습니다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import ClientError

from privacy import redact_payload
from settings import ARTIFACTS_BUCKET, s3
from utils import json_default, now_iso


ANSWER_FILE = "answers.redacted.json"
CONSENT_FILE = "consent.json"
DOCTOR_REVIEW_FILE = "doctor_review.redacted.json"
GUIDE_FILE = "patient_guide.redacted.json"
ONEPAPER_FILE = "onepaper.redacted.json"
TRACE_FILE = "llm_trace.redacted.json"
VALIDATION_TRACE_FILE = "validation_trace.redacted.json"


def require_bucket() -> str:
    """S3 artifact bucket 설정이 없으면 배포 오류를 명확히 드러냅니다."""
    if not ARTIFACTS_BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET environment variable is required.")
    return ARTIFACTS_BUCKET


def date_part(value: str | None) -> str:
    """S3 prefix에 사용할 날짜를 YYYY-MM-DD 형식으로 반환합니다."""
    if value:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).date().isoformat()


def session_prefix(session_id: str, created_at: str | None = None) -> str:
    """세션별 S3 폴더 prefix를 만듭니다."""
    return f"sessions/{date_part(created_at)}/{session_id}/"


def artifact_meta(session_id: str, created_at: str | None = None) -> dict[str, Any]:
    """DynamoDB 세션에 저장할 S3 위치 요약입니다."""
    prefix = session_prefix(session_id, created_at)
    return {
        "bucket": ARTIFACTS_BUCKET,
        "prefix": prefix,
        "answers_key": prefix + ANSWER_FILE,
        "onepaper_key": prefix + ONEPAPER_FILE,
        "guide_key": prefix + GUIDE_FILE,
        "consent_key": prefix + CONSENT_FILE,
        "trace_key": prefix + TRACE_FILE,
        "validation_trace_key": prefix + VALIDATION_TRACE_FILE,
    }


def key_for(session: dict[str, Any], filename: str) -> str:
    """세션의 artifact prefix를 기준으로 파일 key를 계산합니다."""
    artifact = session.get("artifact") or {}
    prefix = artifact.get("prefix") or session_prefix(session.get("session_id"), session.get("created_at"))
    return prefix + filename


def put_json(session: dict[str, Any], filename: str, payload: Any) -> str:
    """payload를 가명처리한 뒤 S3 JSON 객체로 저장하고 key를 반환합니다."""
    bucket = require_bucket()
    key = key_for(session, filename)
    body = json.dumps(
        {
            "stored_at": now_iso(),
            "schema_version": "munjin-artifact-v1",
            "payload": redact_payload(payload),
        },
        ensure_ascii=False,
        default=json_default,
    ).encode("utf-8")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json; charset=utf-8",
    )
    return key


def get_json(session: dict[str, Any], filename: str, default: Any = None) -> Any:
    """S3 JSON artifact를 읽습니다. 객체가 없으면 default를 반환합니다."""
    bucket = require_bucket()
    key = key_for(session, filename)
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return default
        raise
    raw = obj["Body"].read().decode("utf-8")
    data = json.loads(raw)
    return data.get("payload", default)


def load_answers(session: dict[str, Any]) -> dict[str, Any]:
    """문항별 답변 artifact를 읽고, 과거 DDB 저장 구조가 있으면 fallback합니다."""
    answers = get_json(session, ANSWER_FILE, default=None)
    if isinstance(answers, dict):
        return answers
    return dict(session.get("responses") or session.get("question_results") or {})


def save_answers(session: dict[str, Any], answers: dict[str, Any]) -> str:
    """문항별 답변/추출/IR 결과를 S3에 저장합니다."""
    return put_json(session, ANSWER_FILE, answers)


def save_trace(session: dict[str, Any], question_id: str, trace_payload: dict[str, Any]) -> str:
    """질문별 LLM/검증 trace를 S3에 누적 저장합니다."""
    traces = get_json(session, TRACE_FILE, default={})
    if not isinstance(traces, dict):
        traces = {}
    traces[question_id] = trace_payload
    return put_json(session, TRACE_FILE, traces)


def update_question_trace(session: dict[str, Any], question_id: str, orchestration: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    """이미 저장된 답변 artifact에 최종 LangGraph trace를 반영합니다."""
    answers = load_answers(session)
    record = dict(answers.get(question_id) or {})
    if not record:
        return
    record["orchestration"] = orchestration
    record["pipeline_trace"] = trace
    answers[question_id] = record
    save_answers(session, answers)
    save_trace(session, question_id, {"orchestration": orchestration, "pipeline_trace": trace})
