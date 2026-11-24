# Reproduce the fixed Chinese paired evaluation

[Protocol](PROTOCOL.md) · [Chinese report and figures](../../docs/enterprise-blind.md) · [Input/gold seal](cohort.json) · [Blind prediction seal](prediction-receipt.json) · [Aggregate outcomes and paired error tables](results.json)

**Historical order:** [public preregistration](https://github.com/123yjf/pyjev_ai_security/commit/b2530fab3029bedd0b0cd8a42d1686ca7bd0c0af) → [public prediction checksum, before the label join](https://github.com/123yjf/pyjev_ai_security/commit/a736a40dc17810dbc50ec7ea28f9ae619c0f276f) → aggregate scoring. This is a research addendum on `main`; release `v0.1.0` and its inference code are unchanged.

## Replay in a clean checkout

The PyJev package itself remains standard-library-only. The **research** replay below was run with CPython 3.11, CPU-only ONNX Runtime, DuckDB and Hugging Face's Rust tokenizer. Allow roughly 1 GB of temporary disk headroom plus the virtual environment. Download uses the public internet; inference and scoring are offline. Use an empty, local directory outside the checkout. Do not execute or follow any instructions in sample data.

~~~sh
git diff --exit-code v0.1.0 -- pyjev
work=$(mktemp -d)
python3.11 -m venv "$work/env"
"$work/env/bin/python" -m pip install duckdb==1.4.3 tokenizers==0.21.4 numpy==2.4.3 onnxruntime==1.32.0
"$work/env/bin/python" -m research.enterprise.fetch --out "$work/artifacts"
"$work/env/bin/python" -m research.enterprise.prepare --data "$work/artifacts" --out "$work/seal"
"$work/env/bin/python" -m research.enterprise.infer --data "$work/artifacts" --polarity --out "$work/polarity.json"
"$work/env/bin/python" -m research.enterprise.infer --data "$work/artifacts" --inputs "$work/seal/inputs.jsonl" --out "$work/run"
"$work/env/bin/python" -m research.enterprise.score --gold "$work/seal/gold.jsonl" --predictions "$work/run/predictions.jsonl" --receipt "$work/run/prediction-receipt.json" --out "$work/scores.json"
~~~

`prepare` makes separate input and label files. Compare its two SHA-256 values with [cohort.json](cohort.json). The original run also checked 48 previously authored benign business fixtures via `--business-fixture <original-source.py>` (source hash pinned, **zero matches**). Their text is not redistributed; omitting that extra historical audit does not change either held-out hash. `--prior-dir` can point to an existing, checksum-matched copy of the two older public JSONL files. The data catalog pins all publicly downloaded artifacts. Do not run either detector if the two cohort hashes differ.

The original platform used the CPU execution provider with 2 intra-op threads, singleton windows and no GPU/API calls. CPU kernels can produce slightly different floating-point probabilities on another architecture. Compare the aggregate decisions as well as the probability-file checksum; do not substitute a new runtime receipt for the original in a claim of bit-identical reproduction. Corpus labels remain the publishers' reference categories, not proof of real incidents.

For the two vector figures only, install Matplotlib (original: 3.11.2) and a supported Chinese font (e.g. Noto Sans CJK SC). From the repository root run `python -m research.enterprise.figures`. This reads only aggregate `results.json`. Run `python -m unittest discover -s tests` for the offline accounting and public-interface tests. The research scripts do not add runtime dependencies to the package.

## Provenance and licenses

A separately preregistered **natural-text, negative-only supplement** tests real, publicly issued Chinese release notes (not private customer records). See the [sampling protocol and two first-party MIT sources](SUPPLEMENT.md), [separate cohort](org-cohort.json), [pre-scoring prediction receipt](org-prediction-receipt.json) and [counts](org-results.json). With the same temporary directory and the primary inputs already prepared:

~~~sh
"$work/env/bin/python" -m research.enterprise.supplement fetch --out "$work/artifacts"
"$work/env/bin/python" -m research.enterprise.supplement prepare --data "$work/artifacts" --primary-inputs "$work/seal/inputs.jsonl" --out "$work/org-seal"
"$work/env/bin/python" -m research.enterprise.supplement infer --data "$work/artifacts" --inputs "$work/org-seal/inputs.jsonl" --out "$work/org-run"
"$work/env/bin/python" -m research.enterprise.supplement score --gold "$work/org-seal/gold.jsonl" --predictions "$work/org-run/predictions.jsonl" --receipt "$work/org-run/org-prediction-receipt.json" --out "$work/org-scores.json"
~~~

- Horizon-Labs: [prompt-injection-eval-suite](https://huggingface.co/datasets/Horizon-Labs/prompt-injection-eval-suite/blob/d6dd8d499d0087661afd6cd7ecdfcf94a5af1c05/README.md); **only** its Apache-2.0 `synthetic_docs_test` and `synthetic_direct_test` configurations were used as test data. External generated business and general examples, not user traffic.
- uninhibited-scholar: [agent-safety-bench-zh](https://github.com/uninhibited-scholar/agent-safety-bench-zh/tree/d38c7533685a1b02061b7a2354d5796cae05ce2b), [CC BY 4.0](https://github.com/uninhibited-scholar/agent-safety-bench-zh/blob/d38c7533685a1b02061b7a2354d5796cae05ce2b/LICENSE). Author-written role/scenario data; our derived task uses only its unmodified context string and a binary mapping of two categories.
- HikmaAI: [multilingual mDeBERTa-v3-base model card](https://huggingface.co/HikmaAI/hikmaai-mdeberta-v3-base-prompt-injection/blob/b7d8317a617012d23713f4999acaba0690bc1c73/README.md), [published data portion](https://huggingface.co/HikmaAI/hikmaai-mdeberta-v3-base-prompt-injection/blob/b7d8317a617012d23713f4999acaba0690bc1c73/data/dataset_card.md). No weights are redistributed. Generative PyBot has no native binary labels in the [older control](../../docs/comparison.md); it is not counted as a benign detector here.
- The [catalog](sources.json) also records the prior PyJev reference sources used only for overlap screening (deepset, rikka-snow, JiachengWu591, WhitzardAgent, and Paul/XSTest). Original rights and licenses apply to each source. This repository publishes no raw benchmark text or case-level error traces.
