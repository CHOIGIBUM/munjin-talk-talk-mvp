"""Domain-managed symptom alias data for RAG and IR query expansion."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from domain_config import DOMAIN_DATA_DIR, get_domain_pack, selected_domain_pack_id
from utils import load_json_file, normalize_text, unique


ALIAS_DIR = DOMAIN_DATA_DIR / "symptom_aliases"


def _safe_id(value: str, fallback: str = "respiratory") -> str:
    text = str(value or fallback).strip()
    if not text or "/" in text or "\\" in text or ".." in text:
        raise RuntimeError(f"Invalid symptom alias id: {value}")
    return text


def _resolve_configured_path(configured_path: str) -> Path:
    text = str(configured_path or "").strip()
    if not text or "\\" in text or ".." in text:
        raise RuntimeError(f"Invalid symptom alias path: {configured_path}")
    path = Path(text)
    if path.is_absolute():
        raise RuntimeError(f"Symptom alias path must be relative to data/: {configured_path}")
    return DOMAIN_DATA_DIR / path


def _candidate_paths(pack_id: str) -> list[Path]:
    pack = get_domain_pack(pack_id)
    paths: list[Path] = []
    configured = pack.get("symptom_alias_set")
    if configured:
        paths.append(_resolve_configured_path(configured))
    alias_id = _safe_id(str(pack.get("symptom_alias_id") or pack.get("ir_source_id") or pack_id), pack_id)
    paths.append(ALIAS_DIR / f"{alias_id}.json")
    return paths


@lru_cache(maxsize=None)
def load_symptom_alias_payload(pack_id: str | None = None) -> dict[str, Any]:
    safe_pack_id = _safe_id(pack_id or selected_domain_pack_id())
    for path in _candidate_paths(safe_pack_id):
        if not path.exists():
            continue
        payload = load_json_file(path)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid symptom alias file: {path}")
        aliases = payload.get("aliases")
        if not isinstance(aliases, list):
            raise RuntimeError(f"Symptom alias file missing aliases list: {path}")
        return payload
    return {"version": "empty", "aliases": []}


def load_symptom_alias_entries(pack_id: str | None = None) -> list[dict[str, Any]]:
    payload = load_symptom_alias_payload(pack_id)
    return [
        item
        for item in payload.get("aliases", [])
        if isinstance(item, dict) and item.get("canonical_name")
    ]


def symptom_alias_source_files(pack_id: str | None = None) -> list[str]:
    safe_pack_id = _safe_id(pack_id or selected_domain_pack_id())
    labels: list[str] = []
    for path in _candidate_paths(safe_pack_id):
        if path.exists():
            try:
                labels.append(str(path.relative_to(DOMAIN_DATA_DIR)).replace("\\", "/"))
            except ValueError:
                labels.append(str(path))
    return unique(labels)


def aliases_for_name(symptom_name: str, pack_id: str | None = None) -> list[str]:
    name = normalize_text(symptom_name)
    out: list[str] = []
    for entry in load_symptom_alias_entries(pack_id):
        if normalize_text(entry.get("canonical_name")) != name:
            continue
        out.extend(_string_list(entry.get("terms")))
        out.extend(_string_list(entry.get("query_terms")))
    return unique([normalize_text(item) for item in out if normalize_text(item)])


def iter_text_alias_patterns(pack_id: str | None = None) -> list[tuple[str, str]]:
    patterns: list[tuple[str, str]] = []
    for entry in load_symptom_alias_entries(pack_id):
        canonical = normalize_text(entry.get("canonical_name"))
        if not canonical:
            continue
        for pattern in _string_list(entry.get("patterns")):
            patterns.append((pattern, canonical))
        for term in _string_list(entry.get("terms")):
            if term:
                patterns.append((re.escape(term), canonical))
    return patterns


def matched_alias_entries(text: str, pack_id: str | None = None, limit: int = 6) -> list[dict[str, Any]]:
    query = normalize_text(text)
    if not query:
        return []
    matched: list[dict[str, Any]] = []
    for entry in load_symptom_alias_entries(pack_id):
        if _entry_matches_text(entry, query):
            matched.append(entry)
            if len(matched) >= limit:
                break
    return matched


def expand_query_with_symptom_aliases(text: str, pack_id: str | None = None, limit: int = 6) -> str:
    query = normalize_text(text)
    if not query:
        return ""

    expansions: list[str] = []
    for entry in matched_alias_entries(query, pack_id, limit=limit):
        expansions.append(str(entry.get("canonical_name") or ""))
        expansions.extend(_string_list(entry.get("query_terms"))[:8])

    if not expansions:
        return query
    return normalize_text(" ".join([query] + unique([item for item in expansions if item])))


def _entry_matches_text(entry: dict[str, Any], text: str) -> bool:
    for pattern in _string_list(entry.get("patterns")):
        try:
            if re.search(pattern, text):
                return True
        except re.error:
            continue
    for term in _string_list(entry.get("terms")):
        if term and term in text:
            return True
    return False


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [normalize_text(item) for item in value if normalize_text(item)]
