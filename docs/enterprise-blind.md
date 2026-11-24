# Historical enterprise-text study

This **earlier** paired experiment used a frozen predecessor, not pyjev_v1. It is kept to explain why the later study included instruction discussions, quotations and agent narratives. For current results use the [924-text paired comparison](audit-study.md#paired-results).

| Historical stratum | Positive / negative texts | Predecessor misses | HikmaAI misses | Predecessor false alarms | HikmaAI false alarms |
|---|---:|---:|---:|---:|---:|
| Business documents (primary subset) | 17 / 35 | 3/17 (17.6%) | 0/17 (0.0%) | 17/35 (48.6%) | 24/35 (68.6%) |
| All documents including that subset | 21 / 43 | 4/21 (19.0%) | 0/21 (0.0%) | 20/43 (46.5%) | 28/43 (65.1%) |
| Direct questions | 15 / 18 | 4/15 (26.7%) | 2/15 (13.3%) | 4/18 (22.2%) | 0/18 (0.0%) |
| Agent narratives | 153 / 205 | 147/153 (96.1%) | 4/153 (2.6%) | 0/205 (0.0%) | 101/205 (49.3%) |

| Benign purpose | Texts | Predecessor false alarms | HikmaAI false alarms |
|---|---:|---:|---:|
| Risk discussions | 5 | 3/5 (60.0%) | 2/5 (40.0%) |
| Quotations for discussion | 11 | 7/11 (63.6%) | 4/11 (36.4%) |
| Total (disjoint groups) | 16 | 10/16 (62.5%) | 6/16 (37.5%) |

**Do not add overlapping rows.** The primary study comprised 455 texts. Among 16 benign discussions and quotations the predecessor flagged 10, HikmaAI six. Lowering HikmaAI's threshold from 0.5 to 0.005 reduced narrative misses from four to three but increased false alarms from 101 to 111. Published case narratives are not actual tool actions.

A separate, later sample comprised 47 real public release-note entries (24 Ant Design, 23 TDesign Vue Next). These were benign-only controls: the predecessor flagged one, HikmaAI flagged all 47. This measures false alarms on those projects; it does not measure recall or the prevalence of attacks in customer traffic.

| Public release notes | Benign entries | Predecessor false alarms | HikmaAI false alarms |
|---|---:|---:|---:|
| Ant Design | 24 | 1/24 | 24/24 |
| TDesign Vue Next | 23 | 0/23 | 23/23 |

[Historical protocol](../research/enterprise/PROTOCOL.md) · [Aggregate scores](../research/enterprise/results.json) · [Supplement](../research/enterprise/SUPPLEMENT.md) · [Reproduction](../research/enterprise/README.md)
