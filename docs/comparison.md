# Historical control: original PyBot

This is an interface comparison, not the current specialist benchmark. Could an unmodified general-purpose chatbot return the labels required for a review queue? The scoring adapter does not infer verdicts from free-form replies.

The [pinned original implementation](https://github.com/huggingface/pybot/tree/7d63c7fbebb44c7e466e5c8b5c1f341ab767929e) returned scorable labels on **0/2,057** task-prompt inputs and **0/673** verbatim inputs. Texts overlap across these settings; do not add them as unique cases. No label is not a correct negative.

| Dataset | Interface | Scorable / all | Correct / all | Accuracy among scorable | No label / timeout / error |
|---|---|---:|---:|---:|---:|
| Office intent | Historical native interface | 320/320 (100.0%) | 280/320 (87.5%) | 280/320 (87.5%) | 0 / 0 / 0 |
| Office intent | Original PyBot: prompted | 0/320 (0.0%) | 0/320 (0.0%) | Not scorable | 320 / 0 / 0 |
| Office intent | Original PyBot: verbatim | 0/320 (0.0%) | 0/320 (0.0%) | Not scorable | 320 / 0 / 0 |
| Translated scenarios | Historical native interface | 353/353 (100.0%) | 261/353 (73.9%) | 261/353 (73.9%) | 0 / 0 / 0 |
| Translated scenarios | Original PyBot: prompted | 0/353 (0.0%) | 0/353 (0.0%) | Not scorable | 353 / 0 / 0 |
| Translated scenarios | Original PyBot: verbatim | 0/353 (0.0%) | 0/353 (0.0%) | Not scorable | 353 / 0 / 0 |
| Historical Chinese documents | Historical native interface | 1,384/1,384 (100.0%) | 882/1,384 (63.7%) | 882/1,384 (63.7%) | 0 / 0 / 0 |
| Historical Chinese documents | Original PyBot: prompted | 0/1,384 (0.0%) | 0/1,384 (0.0%) | Not scorable | 1341 / 43 / 0 |

A valid indeterminate intent is a semantic answer. A non-label is not. These known suites were used to compare output contracts, not to establish fresh generalization or safety.

## Injection detection and false alarms

| Corpus | Interface | False alarms / scorable negatives | Detections / scorable positives |
|---|---|---:|---:|
| Translated scenarios | Historical native interface | 0/200 (0.0%) | 61/153 (39.9%) |
| Translated scenarios | Original PyBot: prompted | Not scorable | Not scorable |
| Translated scenarios | Original PyBot: verbatim | Not scorable | Not scorable |
| Historical Chinese documents | Historical native interface | 5/61 (8.2%) | 826/1,323 (62.4%) |
| Historical Chinese documents | Original PyBot: prompted | Not scorable | Not scorable |

An empty denominator is unscorable, not zero. These historical native results are not measurements of pyjev_v1.

[Output coverage](figures/baselines.svg) · [Injection detection](figures/detection.svg) · [Intent](figures/intent.svg) · [False reviews](figures/false-reviews.svg)

[Frozen counts](../pyjev/data/pybot-comparison.json) · [Verbatim control](../pyjev/data/pybot-raw-control.json) · [Offline replay](../research/BASELINE_REPLAY.md) · [Current paired study](audit-study.md)
