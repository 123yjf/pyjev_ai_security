# Reproduce the Chinese paired study and CPU timings

Use CPython 3.11 on a system with compatible binary wheels. This is a CPU-only research environment, separate from the standard-library auditor. Reserve several GiB for dependencies and public inputs, including the roughly 355 MB inference artifact. No model API or customer data is used.

~~~sh
lab=$(mktemp -d)
sh research/footprint/venv311.sh research "$lab/env"
PYE="$lab/env/bin/python"
"$PYE" -m pip --isolated --disable-pip-version-check install --no-cache-dir --no-compile --only-binary=:all: --index-url https://pypi.org/simple -r research/footprint/requirements-cpu311.txt
"$PYE" -m pip check
~~~

Choose **one** path. Each output directory must be new.

~~~sh
# Fetch the pinned public source files and verify their hashes.
"$PYE" -s -m research.footprint.reproduce --out "$lab/run-online" --timings

# Or use verified raw public inputs from an earlier run; no network.
"$PYE" -s -m research.footprint.reproduce --offline --asset-cache /path/to/previous --asset-cache /path/to/current --out "$lab/run-offline" --timings
~~~

The runner verifies 44 source assets, rebuilds the older deduplication sets (455 and 47 records), seals 924 texts and their labels, runs the frozen detectors, then scores them. Cached predictions are not an input. Original private deduplication controls (48 texts) are not redistributed; the recorded offline replay regenerated the same public input and label digests without them.

| Artifact | What to verify |
|---|---|
| `replay-receipt.json` | 924 rebuilt inputs, no reused predictions and matching aggregate scores. The reference CPU replay also matched the prediction bytes and the independent SQL check. |
| `local-tallies.json` | Review counts by stratum, not just a successful exit. For example, injection misses were 413 vs. 71, ordinary-task false alarms 4 vs. 36 (pyjev_v1 vs. HikmaAI). |
| `local-footprint.json` | With `--timings`, inspect per-process measurements. Repeated timings do not increase the number of unique texts. Milliseconds are hardware-dependent. |

[Recorded replay](replay-receipt.json) · [Recorded Apple M4 timings](observed-m4.json) · [Research report](../../docs/audit-study.md)
