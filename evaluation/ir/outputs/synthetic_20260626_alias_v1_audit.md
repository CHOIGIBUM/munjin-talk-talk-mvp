# Synthetic Alias V1 Evaluation Audit - 2026-06-26

## Verdict

The alias V1 result is useful as an engineering ablation, but it is not a clean
blind benchmark. There is no evidence of a direct hard cheat such as passing
`case_id`, `gold_symptoms`, or hidden labels into runtime matching. However,
there is evaluation leakage: alias and few-shot content now contains many exact
strings from the synthetic data generator, and the locked holdout was inspected
during failure analysis. Treat the reported holdout numbers as contaminated.

## Why Candidate Recall Can Be High While F1 Is Low

Fast candidate-only IR measures only whether the correct symptom is somewhere in
the top-k candidates. It does not prove the final answer is correct.

For synthetic cases without explicit spans, `run_ir_eval.py` falls back to one
full-case active span:

- `source_quote = case_text(case)`
- `normalized_text = case_standard_text(case)`
- `status = "있음"`
- `type = "symptom"`

That means the fast IR score often queries with the whole patient answer instead
of the LLM-extracted active symptom spans. This is a candidate coverage smoke
test, not end-to-end pipeline performance.

The full pipeline F1 is lower because it also depends on:

- LLM extraction producing the right active spans.
- Resolved or negated symptoms being excluded.
- The extracted span name and status passing schema validation.
- The deterministic matcher or linker choosing the right candidate, not only
  retrieving it.

The 30-case mini pipeline still had 9 failure rows:

| Case | Failure | Gold | Prediction |
| --- | --- | --- | --- |
| syn_0005 | partial miss + false positive | 가슴 두근거림 | 가슴 답답 |
| syn_0009 | partial miss + false positive | 거품이 섞인 가래, 호흡곤란 | 가래, 호흡곤란 |
| syn_0011 | no extracted spans | 흉부압박감 | none |
| syn_0013 | validator failed | 설사 | none |
| syn_0018 | missing gold | 두통, 하지부종 | 하지부종 |
| syn_0020 | pipeline error | 검은색 가래, 재채기, 콧물 | none |
| syn_0028 | no extracted spans | 부정맥, 운동 시 호흡곤란 | none |
| syn_0029 | pipeline error | 빈맥, 흉통 | none |
| syn_0030 | partial miss + false positive | 권태감, 눈꼽, 호흡곤란 | 기운없음, 눈꼽, 호흡곤란 |

So the main remaining gap is not just candidate retrieval. It is extraction,
validation, and final candidate selection.

## Leakage Findings

An automated overlap check found:

- Alias/query terms checked: 247
- Exact alias/query terms present in the generator source: 117
- Alias `terms` hits: 78
- Alias `query_terms` hits: 39
- Few-shot strings checked: 127
- Exact few-shot strings present in the generator source: 5

Examples of overlap include:

- `심장이 쿵쿵`
- `맥이 너무 빨리`
- `맥이 들쑥날쑥`
- `가슴을 꽉 누르는`
- `가래에 거품`
- `거품 섞인 가래`
- `숨쉴 때 쌕쌕`
- `물 마시면 사레`

The added few-shot examples also include exact generator phrases such as:

- `가래에 거품이 보입니다`
- `가슴을 꽉 누르는 느낌입니다`

This does not mean production inference is cheating. It does mean the synthetic
benchmark can no longer be used as a blind generalization claim after these
phrases were added.

## Correct Interpretation

Acceptable claim:

- Alias V1 improves candidate coverage on the current synthetic generator and
  reduces known development misses.

Not acceptable claim:

- The system has achieved about 99% real-world performance.
- The locked holdout remains a blind benchmark.

The `0.9857` full synthetic Recall@20 should be described as:

> synthetic template-covered fast IR candidate recall

not as final pipeline F1 or production accuracy.

## Clean Follow-Up Protocol

1. Freeze the current code, alias file, few-shot file, and prompt set.
2. Generate a new blind eval split after the freeze.
3. Use different expression templates or human-authored paraphrases not copied
   into alias/few-shot data.
4. Do not inspect validation or holdout failures until after reporting the
   frozen score.
5. Report three separate metrics:
   - fast full-text candidate coverage,
   - pipeline-generated-span candidate coverage,
   - end-to-end pipeline F1.
6. Keep the current 1000-case synthetic set as public development data only.
