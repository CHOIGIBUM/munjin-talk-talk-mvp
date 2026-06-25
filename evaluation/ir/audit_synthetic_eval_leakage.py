"""Audit synthetic IR evaluation for template leakage.

This script checks whether evaluation-time helper data contains exact strings
from the synthetic dataset generator. Exact overlap is not automatically a
runtime cheat, but it means the corresponding score should be treated as a
development ablation rather than a clean blind benchmark.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ALIAS_PATH = Path("backend/serverless/src/data/symptom_aliases/respiratory.json")
DEFAULT_FEWSHOT_PATH = Path("backend/serverless/src/data/fewshots/respiratory/symptom_hint.json")
DEFAULT_GENERATOR_PATH = Path("evaluation/ir/dataset_generation/generate_synthetic_ir_dataset.py")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_alias_terms(alias_data: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for entry in alias_data.get("aliases", []):
        if not isinstance(entry, dict):
            continue
        canonical = str(entry.get("canonical_name") or "")
        for field in ("terms", "query_terms"):
            for value in entry.get(field, []):
                if isinstance(value, str) and value.strip():
                    rows.append((canonical, field, value.strip()))
    return rows


def iter_strings(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, (*path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, (*path, str(index)))
    elif isinstance(value, str):
        yield path, value


def collect_fewshot_strings(fewshot_data: dict[str, Any], min_chars: int) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    examples = fewshot_data.get("examples", [])
    if not isinstance(examples, list):
        return rows
    for example in examples:
        if not isinstance(example, dict):
            continue
        title = str(example.get("title") or "(untitled)")
        for path, value in iter_strings(example):
            if len(value.strip()) >= min_chars:
                rows.append((title, ".".join(path), value.strip()))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--alias-path", type=Path, default=DEFAULT_ALIAS_PATH)
    parser.add_argument("--fewshot-path", type=Path, default=DEFAULT_FEWSHOT_PATH)
    parser.add_argument("--generator-path", type=Path, default=DEFAULT_GENERATOR_PATH)
    parser.add_argument("--min-fewshot-chars", type=int, default=8)
    parser.add_argument("--show", type=int, default=30)
    args = parser.parse_args()

    root = args.repo_root
    alias_path = root / args.alias_path
    fewshot_path = root / args.fewshot_path
    generator_path = root / args.generator_path

    generator_text = generator_path.read_text(encoding="utf-8")
    alias_terms = collect_alias_terms(read_json(alias_path))
    alias_hits = [row for row in alias_terms if row[2] in generator_text]

    fewshot_strings = collect_fewshot_strings(read_json(fewshot_path), args.min_fewshot_chars)
    fewshot_hits = [row for row in fewshot_strings if row[2] in generator_text]

    print("Synthetic evaluation leakage audit")
    print(f"alias_terms={len(alias_terms)}")
    print(f"exact_alias_terms_in_generator={len(alias_hits)}")
    print(f"alias_hit_fields={dict(Counter(row[1] for row in alias_hits))}")
    print(f"fewshot_strings_checked={len(fewshot_strings)}")
    print(f"exact_fewshot_strings_in_generator={len(fewshot_hits)}")
    print()
    print("Alias overlap examples:")
    for canonical, field, term in alias_hits[: args.show]:
        print(f"- {canonical} [{field}]: {term}")
    print()
    print("Few-shot overlap examples:")
    for title, path, value in fewshot_hits[: args.show]:
        print(f"- {title} [{path}]: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
