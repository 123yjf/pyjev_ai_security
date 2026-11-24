# PyJev AI Security · model card

## Identity and scope

Version 0.1.0, Apache-2.0. PyJev is a task-specific post-response classifier, not an LLM or chatbot. Inference is implemented in Python's standard library. **Pure Python inference does not mean “no learned parameters”**: this release includes both deterministic rules and fitted numerical parameters. Original PyBot is a separate general-purpose rule-based chatbot; Jev is not a component of this release.

| Component | Artifact | Published SHA-256 |
|---|---|---|
| Bilingual signal detector · checkpoint 323 | [rulebook](pyjev/data/rulebook.json) | `d98dd4e58ec4670abaea9fd32c42adef73048bcc07b1e7b6b7e7a37e13a2ec42` |
| Chinese speech-act classification · calibrated operating threshold | [intent head](pyjev/data/head.json) | `9bbc915995945b5cbf3f4e2f9ef35254ac00e331b1896e2ebf15a27e84661ded` |
| Frozen office / translation / historical study | [aggregate](pyjev/data/results.json) | `d4e354aa67fe216611aeb609de62a6314389a5fba843fdee1a33f1466891d037` |

The signal component uses two anchor vocabularies and 16,000 fitted features; the speech-act head uses 1,316 fitted features plus a conservative outer-language-frame decision. [Training, ablations and dataset attribution](research/README.md). Local SHA checks guard against accidental mismatch, not against an adversary who can replace both package code and data; use a trusted distribution source.

## Intended use

Offline research, review-queue analysis, or opt-in asynchronous annotation of text that the operator is already entitled to process. Public examples are synthetic office tasks. The package sends nothing externally. It is not designed to grant/revoke tool permissions, intercept a network request, identify a model or a person, detect every secret, or send incident mail.

## Input, language and evidence limits

Each call sees **one flat text only**. No trusted role, provenance, recipient, execution receipt or surrounding turn is supplied. The speech-act evaluation is Chinese; the binary signal layer uses aligned language blocks and has dataset-specific evaluation. Do not assume equivalent performance for every dialect, language, modality, document type or shift in traffic. “Unclear” may be the most useful supported decision for an embedded document. No calibrated probability is exposed. A detected request to act does not establish authorization or execution.

## Operating point

The default queue suggestion retains all raw positives. A separate experimental field can downgrade a clearly editorial phrase to record-only; the original signal is still present. This experimental route was **not promoted**. In 120 authored discussions its false reviews decreased by three, all in one topic across three frames. No reduction was seen on the external-translation normal cohort or the historical Chinese normal cohort. The translation corpus still had 92 missed positive cases of 153. These limitations matter more than a pooled accuracy figure.

For current version-specific counts see the [research figures](README.md), [original comparator report](docs/comparison.md), [input/output contract](docs/contract.md) and [research limitations](research/README.md). Before any production decisions, use independently annotated, representative inputs and separately validate downstream authorization and execution evidence.
