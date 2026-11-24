# Model card: pyjev_v1

**Intended use:** local, post-response annotation for an enterprise review queue. The auditor does not decide authorization, identify a provider, execute a tool, block a request, redact personal data or send alerts.

| Property | Description |
|---|---|
| Input | One authorized Unicode text, up to 32,768 characters; no trusted actor, document provenance or client execution receipt. |
| Output | Injection signal, speaker intent, review route and review flag. No calibrated probability. |
| Implementation | Bilingual lexical anchors and learned sparse weights, followed by discourse and evidence rules. Local standard-library inference; no GPU or network call. |
| Evaluation | 924 public Chinese texts; offline CPU comparison with HikmaAI INT8. The English examples demonstrate the API, not measured English accuracy. |
| Main limitation | pyjev_v1 missed 413 of 450 injected tool responses and recognized only 18 of 48 discussions or quotations. Never interpret a negative result as authorization. |
| License | Apache-2.0 for this code and its parameters; see [third-party notices](NOTICE). |

**Artifact integrity.** [Signal weights](pyjev/data/rulebook.json) (SHA-256 `d98dd4e58ec4670abaea9fd32c42adef73048bcc07b1e7b6b7e7a37e13a2ec42`) and [speech-act weights](pyjev/data/head.json) (`9bbc915995945b5cbf3f4e2f9ef35254ac00e331b1896e2ebf15a27e84661ded`) are checked locally. These checks detect mismatches, not replacement of both code and parameters by an untrusted distributor.

[Research and timings](docs/audit-study.md) · [Usage and output meanings](docs/start-local.md) · [Frozen evaluation protocol](research/scope_study/PROTOCOL.md)
