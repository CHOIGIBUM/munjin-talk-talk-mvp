# Synthetic IR Alias V1 Test Report - 2026-06-26

> Audit warning: this report is a development ablation, not a clean blind
> benchmark. Alias and few-shot content overlap heavily with the synthetic
> generator templates, and the locked holdout was inspected during failure
> analysis. See `synthetic_20260626_alias_v1_audit.md`.

## Change Summary

- Added domain-managed symptom alias data at `backend/serverless/src/data/symptom_aliases/respiratory.json`.
- Added `symptom_aliases.py` loader.
- Connected alias data to:
  - `clinical_terms.IR_TEXT_ALIASES`
  - RAG alias hints and trace source files
  - BM25 symptom document alias text
  - IR query expansion through `build_symptom_query`
- Added focused `symptom_hint` few-shot examples for:
  - palpitation vs tachycardia vs irregular rhythm
  - foam/black sputum and wheezing
  - chest pressure vs broad chest discomfort
- Increased `symptom_hint` few-shot render limit from 3 to 5.

## Fast Candidate-Only IR

This test does not run the final LLM linker. It checks whether the gold symptom is present in top-k candidates.

| Split | Cases | Before R@5 | After R@5 | Before R@10 | After R@10 | Before R@20 | After R@20 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dev | 300 | 0.7139 | 0.9200 | 0.7972 | 0.9644 | 0.8756 | 0.9900 |
| Validation | 200 | 0.6492 | 0.9058 | 0.7383 | 0.9525 | 0.8408 | 0.9783 |
| Locked holdout | 500 | 0.6843 | 0.9210 | 0.7747 | 0.9600 | 0.8510 | 0.9860 |
| Full synthetic | 1000 | 0.6862 | 0.9177 | 0.7742 | 0.9598 | 0.8563 | 0.9857 |

NegativeHit@20 remains 0.2500 in candidate-only tests because 25% of synthetic cases intentionally contain an absent/resolved symptom in the same full-case text. The operational pipeline sends only active spans to IR, so this value is mainly a stress indicator for full-text candidate retrieval rather than final false positives.

## Full Mini Pipeline

Input: first 30 cases from `synthetic_dev_300.json`

| Metric | Before | Alias only | Alias + few-shot |
| --- | ---: | ---: | ---: |
| Pipeline Micro F1 | 0.6582 | 0.7901 | 0.8000 |
| Pipeline Macro F1 | 0.6356 | 0.7278 | 0.7611 |
| Pipeline Exact match | 0.5667 | 0.6667 | 0.7000 |
| Pipeline FPR | 0.2353 | 0.1111 | 0.0857 |
| Pipeline FNR | 0.4222 | 0.2889 | 0.2889 |
| Pipeline validator pass | 0.9333 | 0.9000 | 0.9000 |

G variant on pipeline-generated spans:

| Metric | Before | Alias only | Alias + few-shot |
| --- | ---: | ---: | ---: |
| Candidate Recall@3 | 0.8278 | 0.9278 | 0.9389 |
| Candidate Recall@5 | 0.9056 | 1.0000 | 1.0000 |
| Candidate Recall@20 | 0.9222 | 1.0000 | 1.0000 |
| Linker Micro F1 | 0.8276 | 0.8235 | 0.8471 |
| Linker Macro F1 | 0.8611 | 0.8333 | 0.8611 |
| Linker Exact match | 0.8000 | 0.8000 | 0.8333 |
| Linker FPR | 0.1429 | 0.1250 | 0.1000 |
| Linker FNR | 0.2000 | 0.2222 | 0.2000 |

## Remaining Issues

- Fast IR misses after alias V1 are now much smaller and concentrated around `복부팽만감`, `객혈`, `부정맥`, `구토`, `호흡곤란`, and a few low-frequency expressions.
- Pipeline failures still include cases where LLM extraction fails after retries, especially multi-symptom dense answers.
- The full-text candidate-only negative hit rate is expected to remain high until the evaluator separates active and absent spans before candidate retrieval.

## Reproduction Commands

```powershell
python evaluation\ir\run_ir_eval.py --input evaluation\ir\data\synthetic\synthetic_dev_300.json --output-dir evaluation\ir\outputs\synthetic_20260626_alias_v1_dev_fast\ir_candidate_only --top-k 20 --variants C --skip-llm-judge
python evaluation\ir\run_ir_eval.py --input evaluation\ir\data\synthetic\synthetic_validation_200.json --output-dir evaluation\ir\outputs\synthetic_20260626_alias_v1_validation_fast\ir_candidate_only --top-k 20 --variants C --skip-llm-judge
python evaluation\ir\run_ir_eval.py --input evaluation\ir\data\synthetic\synthetic_locked_holdout_500.json --output-dir evaluation\ir\outputs\synthetic_20260626_alias_v1_holdout_fast\ir_candidate_only --top-k 20 --variants C --skip-llm-judge
python evaluation\ir\run_ir_eval.py --input evaluation\ir\data\synthetic\synthetic_1000.json --output-dir evaluation\ir\outputs\synthetic_20260626_alias_v1_fast\ir_candidate_only --top-k 20 --variants C --skip-llm-judge
python evaluation\ir\run_eval_suite.py --input evaluation\ir\data\synthetic\synthetic_dev_300.json --output-dir evaluation\ir\outputs\synthetic_20260626_alias_v1_fewshot_dev_full30 --limit 30 --top-k 20 --variants G
```
