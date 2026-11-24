# Paired evaluation: can pyjev_v1 distinguish instruction use from mention?

**Finding:** pyjev_v1 issued fewer false alarms on ordinary tasks but missed 413 of 450 injected tool responses. The same texts were given to both detectors. A flag means a review suggestion, not a confirmed attack, execution or breach.

### Table 1. Misses and false alarms

| Test material | Error type | Texts | pyjev_v1 | HikmaAI |
|---|---|---:|---:|---:|
| Injected tool responses | Miss | 450 | 413 | 71 |
| Clean web templates | False alarm | 15 | 0 | 14 |
| Ordinary tool tasks | False alarm | 401 | 4 | 36 |
| Instruction discussions | False alarm | 27 | 16 | 19 |
| Quoted instructions | False alarm | 21 | 10 | 5 |

Lower is better. The 450 injected responses come from 15 templates; the 15 clean templates are a small sample. Ten further public incident summaries were scored separately: of eight labeled injection-related, pyjev_v1 missed two and HikmaAI missed three. Neither flagged the two remaining summaries. Recognizing a report is not evidence that an embedded instruction was executed.

### Table 2. Speaker intent

| Human label | Texts | pyjev_v1 correct | Other answers |
|---|---:|---:|---:|
| Discussion or quotation | 48 | 18 | 30 |
| Request to act | 21 | 8 | 13 |
| Indeterminate intent | 3 | 3 | 0 |

The 30 remaining discussions received 26 indeterminate predictions and four incorrect action predictions. Intent labels were assigned by a single reviewer. HikmaAI does not predict speaker intent; its binary label cannot substitute for one.

### Historical regression, not a new blind test

All 481 designated historical positives still reached review. On 153 historical positive agent narratives, seven additional cases were detected and 140 were still missed. The older office-intent exercise scored 250/320, a loss of 30 correct answers. These checks cannot improve or expand the blind-test denominator.

[Publication tables](audit-study.md#paired-results) · [Frozen aggregate scores](../research/scope_study/blind-results.json) · [Historical counts](../research/scope_study/regression.json) · [Protocol](../research/scope_study/PROTOCOL.md) · [Reproduce](../research/footprint/README.md)
