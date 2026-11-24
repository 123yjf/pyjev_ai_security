# Contributing

1. Reproduce with a harmless synthetic example and note the version, expected label, observed label, and whether the case is discussion, an action request, or unknown. Do not submit customer conversations.
2. Keep `signal`, intent and execution evidence independent. Runtime dependencies and remote calls require a design discussion; the default package runs offline.
3. Run `python -m unittest discover -s tests -v` and `python -m pyjev bench --json`. Use the public replay protocols for research changes. Preserve aggregates, corpus versions and denominators; report misses and abstentions. A previously published test suite becomes a regression suite, not a new blind test.
4. Do not change frozen weights or charts independently: cite the new checkpoint, freeze the protocol, recompute the evidence and regenerate figures. A new default policy requires separate evidence.

## Reproducibility gate for documentation and experimental claims

- Start from a newly extracted source tree and a venv without system site packages. Copy the commands **as printed**. Keep the no-pip auditor separate from the pinned, CPU-only research environment. Record Python, platform and what was downloaded versus supplied from a verified public cache.
- For every new output example, include the input, exact native result, human interpretation, version, and what the result cannot establish. Run `python -s -m research.footprint.smoke` and the full local test suite. Never include customer text or credentials.
- For a benchmark claim, label the question, comparison, denominator, units and limits. Pair quality with cost. Rebuild decisions from source inputs, not archived answers; report aggregate and byte-for-byte agreement separately. Runtime, resource, security policy, and human-review outcomes are different claims. See the [runtime deployment guide](docs/start-local.md) and [CPU study reproduction](research/footprint/README.md).
