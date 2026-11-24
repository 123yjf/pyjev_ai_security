# Contributing

1. Reproduce with a harmless synthetic example and note the version, expected label, observed label, and whether the case is discussion, an action request, or unknown. Do not submit customer conversations.
2. Keep `signal`, intent and execution evidence independent. Runtime dependencies and remote calls require a design discussion; the default package runs offline.
3. Run `python -m unittest discover -s tests -v` and `python -m pyjev bench --json`. Use the public replay protocols for research changes. Preserve aggregates, corpus versions and denominators; report misses and abstentions. A previously published test suite becomes a regression suite, not a new blind test.
4. Do not change frozen weights or charts independently: cite the new checkpoint, freeze the protocol, recompute the evidence and regenerate figures. A new default policy requires separate evidence.
