"""Question-level semantic parsing compatibility endpoint.

운영 문항 처리는 `/process-answer`의 LangGraph 파이프라인이 담당합니다.
이 파일은 `/extract` 단독 디버그 endpoint를 유지하기 위한 호환 경로입니다.
프롬프트, RAG 참고 문맥, schema/source_quote 검증은 운영 파이프라인과 같은
구성 요소를 재사용하지만, graph trace 저장과 IR/원페이퍼 갱신은 수행하지 않습니다.
"""

import hashlib

from extraction_prompts import (
    build_extraction_prompt,
    build_extraction_repair_note,
    select_extraction_model,
)
from extraction_schema import normalize_extraction_output
from llm import call_bedrock_json_with_meta
from rag_context import retrieve_intake_rag_context
from settings import (
    EXTRACTION_RETRY_ATTEMPTS,
    MAX_LLM_TOKENS,
)
from utils import normalize_visit_type


def extract_question(body):
    """Bedrock LLM extraction을 수행하고 실패를 rule-base로 숨기지 않습니다."""
    transcript = (body.get("transcript") or "").strip()
    try:
        return extract_question_bedrock(body)
    except Exception as exc:
        return extraction_error(transcript, "bedrock_error", str(exc))


def extract_question_bedrock(body):
    """LLM 추출을 수행하고 schema/source_quote 검증 실패 시 bounded retry를 돌립니다."""
    question_type = body.get("question_type") or body.get("questionType")
    question_id = body.get("question_id") or body.get("questionId") or ""
    visit_type = normalize_visit_type(body.get("visit_type") or body.get("visitType"))
    transcript = (body.get("transcript") or "").strip()
    if not transcript:
        return {"spans": [], "structured": {}, "transcript": "", "method": "bedrock_nova"}

    model_id = select_extraction_model(visit_type, question_id, question_type)
    rag_context = retrieve_intake_rag_context(transcript, question_type=question_type)
    repair_note = ""
    last_normalized = None
    last_raw_text = ""
    last_errors = []
    attempts = max(1, EXTRACTION_RETRY_ATTEMPTS)

    for attempt in range(1, attempts + 1):
        prompt = build_extraction_prompt(
            visit_type,
            question_id,
            question_type,
            transcript,
            repair_note=repair_note,
            rag_context_note=rag_context.get("prompt_note") or "",
        )
        obj, raw_text, chain_meta = call_bedrock_json_with_meta(prompt, model_id, MAX_LLM_TOKENS)
        normalized, validation_errors = normalize_extraction_output(obj, transcript, question_id, question_type)
        last_normalized = normalized
        last_raw_text = raw_text
        last_errors = validation_errors
        if not validation_errors:
            break
        repair_note = build_extraction_repair_note(validation_errors, transcript)

    last_normalized = last_normalized or {"spans": [], "structured": {}}
    last_normalized.update({
        "transcript": transcript,
        "method": "bedrock_nova",
        "validator_passed": not last_errors,
        "llm_meta": {
            "model_id": model_id,
            "raw_sha256": hashlib.sha256(last_raw_text.encode("utf-8")).hexdigest(),
            "langchain": chain_meta,
            "rag_context": summarize_rag_context(rag_context),
            "validation_errors": last_errors,
            "attempts": attempt,
            "retry_loop": "standalone_schema_quote_repair",
        },
    })
    return last_normalized


def summarize_rag_context(rag_context):
    """디버그 응답에 긴 prompt 문구 대신 RAG 출처 요약만 남깁니다."""
    return {
        "retriever": rag_context.get("retriever"),
        "source_files": rag_context.get("source_files") or [],
        "alias_hint_count": len(rag_context.get("alias_hints") or []),
        "symptom_reference_count": len(rag_context.get("symptom_references") or []),
    }


def extraction_error(transcript, method, message):
    """LLM 필수 모드에서 실패했을 때 rule-base로 숨기지 않고 명시적으로 반환합니다."""
    return {
        "spans": [],
        "structured": {},
        "transcript": transcript,
        "method": method,
        "validator_passed": False,
        "error": message,
    }
