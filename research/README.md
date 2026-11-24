# Research guide

Start with the [research report](../docs/audit-study.md), then check the [paired scores](scope_study/blind-results.json) and [offline reproduction guide](footprint/README.md). Public aggregates contain no individual customer inputs or missed-item lists.

| Question | Evidence | What it establishes |
|---|---|---|
| Does a generic chatbot emit usable audit labels? | [Original PyBot controls](../docs/comparison.md) | Output-contract coverage, not chatbot knowledge or attack success. |
| Why add sparse weights to lexical rules? | [Component counts](signal-controls.json) | On 1,323 historical positives, detections rose from 345 to 826; false alarms on 61 normals rose from two to five. These are historical ablations, not a new blind result. |
| Why measure discussion and quotation separately? | [Historical enterprise study](../docs/enterprise-blind.md) | Ordinary writing can contain instruction-shaped text. Analyze false-review burden separately from detection. |
| What does pyjev_v1 detect? | [Paired Chinese study](scope_study/README.md) | Misses, false alarms and speaker-intent judgments from the same fixed inputs. |
| How much does inference cost? | [Observed M4 footprint](footprint/observed-m4.json) | Short-text latency and peak process memory on one CPU configuration; not gateway traffic capacity. |

Training and selection were separate from frozen evaluation. The published program uses fitted sparse parameters as well as deterministic rules. After a blind set is revealed, treat it only as regression data. Public source availability does not guarantee exclusion from undisclosed pretraining. Do not infer authorization, model identity, attachment safety or real execution from a text-level label.

[Historical calibration](calibration.json) · [Frozen aggregate results](../pyjev/data/results.json) · [Model card](../MODEL_CARD.md) · [Source and licensing notices](../NOTICE)
