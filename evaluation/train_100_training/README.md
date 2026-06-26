# Train 100 Artifact Build

This folder rebuilds the runtime respiratory domain artifacts from the clean
`evaluation/generated/train_100/cases.jsonl` dataset only.

The word "train" here means artifact construction for the current MVP pipeline:

- domain pack symptom slots
- IR alias hints
- safety flag definitions
- prompt few-shot examples
- provenance report

It does not fine-tune a model, and it does not use any held-out evaluation or
test data.

## Command

```powershell
cd C:\Users\CGB\munjin-talk-talk-mvp
python evaluation\train_100_training\build_train_artifacts.py
```

## Inputs

- `evaluation/generated/train_100/cases.jsonl`
- `backend/serverless/src/data/symptom_index.json`

## Outputs

- `backend/serverless/src/data/domain_packs/respiratory.json`
- `backend/serverless/src/data/fewshots/respiratory/*.json`
- `evaluation/train_100_training/training_report.json`

