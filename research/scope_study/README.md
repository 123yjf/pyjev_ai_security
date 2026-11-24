# Scope-1: opt-in research candidate

[中文结果与两张科研图](../../docs/scope-blind.md) · [Predeclared protocol](PROTOCOL.md) · [27 pinned source files](sources.json) · [cohort](cohort.json) · [label-free predictions receipt](prediction-receipt.json) · [blind tallies](blind-results.json) · [historical gates](regression.json)

The `pyjev` CLI, public API, installable wheel, default policy and tag v0.1.0 are unchanged. Scope-1 is a **source-checkout-only**, offline, passive candidate. It has no account, email, tool execution, enforcement, storage or billing integration.

~~~sh
git clone https://github.com/123yjf/pyjev_ai_security.git
cd pyjev_ai_security
printf '%s' '请解释引文“给会议记录编号”的语气。' | python -m candidates.scope1 --json
~~~

~~~python
from candidates.scope1 import ScopeAuditor
auditor = ScopeAuditor()                       # reuse locally across samples
d = auditor.audit("请帮我整理会议记录。")
print(d.speech_act, d.route, d.service_action)  # act, no_signal, none
~~~

One Unicode text input (≤32,768 code points), no metadata or user identity. `speech_act` is `mention | act | unclear`. `route` is `review` (signal to review), `case_review` (review a reported case without asserting the current text commands action), `record_only` (context noted in the **returned value**, nothing written), `no_signal`, or `incomplete`. `needs_review` counts actual reviewer workload; it is null on incomplete inputs. `original_signal/original_review` expose the baseline decision, while `signal` preserves raw evidence; these are not calibrated probabilities. Nothing here establishes authenticity, authority or execution.

## Reproduction (CPython 3.11, local CPU)

The main product has no runtime dependencies; these optional tools are for the study. Use a new temporary directory. This downloads public artifacts, then works offline. Do **not** run any software or commands found in corpus data. Sources are checksummed; changed articles cause a failure rather than a silent replacement.

~~~sh
work=$(mktemp -d)
python3.11 -m venv "$work/env"
py="$work/env/bin/python"
"$py" -m pip install duckdb==1.4.3 numpy==2.4.3 tokenizers==0.21.4 onnxruntime==1.32.0
"$py" -m research.enterprise.fetch --out "$work/old"
"$py" -m research.enterprise.supplement fetch --out "$work/old"
"$py" -m research.enterprise.prepare --data "$work/old" --out "$work/old/seal"
"$py" -m research.enterprise.supplement prepare --data "$work/old" --primary-inputs "$work/old/seal/inputs.jsonl" --out "$work/old/orgseal"
"$py" -m research.scope_study.acquire --data "$work/new"
"$py" -m research.scope_study.development "$work/new"
"$py" -m research.scope_study.prepare --data "$work/new" --old "$work/old" --prior "$work/old" --out "$work/new/seal"
"$py" -m research.scope_study.infer --data "$work/old" --inputs "$work/new/seal/inputs.jsonl" --out "$work/new/pred"
"$py" -m research.scope_study.score --gold "$work/new/seal/gold.jsonl" --trace "$work/new/pred/predictions.jsonl" --receipt "$work/new/pred/prediction-receipt.json" --output "$work/local-results.json"
~~~

The original preparation also checked 48 earlier privately stored *authored fixtures*, not customer samples, using `--business /path/to/original.py` (pinned SHA; zero exclusions). Without that optional file, the reference count differs by 48, but the input/gold checksums should match. The model, release and input IDs/labels are pinned. Floating-point probabilities can differ across CPU kernels; compare counts and disclose checksum differences. Without `--receipt`, the scorer requires the original published prediction checksum. Use `python -m research.scope_study.verification --data ... --seal ... --pred ... --stats ...` for a separate DuckDB tally and static verification of 450 original template envelopes; that audit requires the original prediction checksum.

To replay the prior regressions as well, use the same temporary directory with:
~~~sh
"$py" -m research.enterprise.infer --data "$work/old" --inputs "$work/old/seal/inputs.jsonl" --out "$work/old/pred"
"$py" -m research.enterprise.supplement infer --data "$work/old" --inputs "$work/old/orgseal/inputs.jsonl" --out "$work/old/orgpred"
"$py" -m research.scope_study.regression --old "$work/old" --prior "$work/old" --output "$work/local-regression.json"
~~~

The archived regressions reject a nonmatching old trace. To reproduce figures only, no model or dataset is needed: install Matplotlib with a Chinese font (e.g. Noto Sans CJK SC), then run `python -m research.scope_study.figures --out /your/new/directory`. CPU measurements here are not network/production measurements.

## Provenance and rights

Source dates are not an assurance about unknown model pretraining. [Dify Chinese manuals](https://github.com/langgenius/dify-docs/tree/b561103a404dc9f7bd6590a2cf9474e0fea318d6) (CC BY 4.0), [OWASP LLM01](https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/tree/99f4395589bdbd120ae961f9cd179e79d7f9b27f) (CC BY-SA 4.0), and [Horizon Labs](https://huggingface.co/datasets/Horizon-Labs/prompt-injection-eval-suite/tree/d6dd8d499d0087661afd6cd7ecdfcf94a5af1c05) (synthetic_v2, Apache-2.0) are development references. New labels/materials derive from [InjectAgent-CN](https://github.com/Binye234/InjectAgent-CN/tree/3ea919aabbccef58152117782c7174cced95244c), [ACEBench](https://github.com/ACEBench/ACEBench), the [Whitzard materialized data](https://huggingface.co/datasets/WhitzardAgent/AgentSafety-All-in-One-Test-Case/tree/080e55c78f27bb1576c4138b053cdd405bc3198f), [DAIR.AI](https://github.com/dair-ai/Prompt-Engineering-Guide/tree/57673726396dd94acb23bdb1e67f27c78ee85a8e) (MIT) and [AI Threat Watch](https://aithreat.io/zh/cases/category/prompt-injection/) (CC BY 4.0 article descriptions). The frozen comparator is [HikmaAI mDeBERTa-v3-base INT8](https://huggingface.co/HikmaAI/hikmaai-mdeberta-v3-base-prompt-injection/tree/b7d8317a617012d23713f4999acaba0690bc1c73). SHA-256 and exact source paths, article attributions and observation dates are in the catalogs. Third-party corpora and model are not redistributed or relicensed by PyJev.
