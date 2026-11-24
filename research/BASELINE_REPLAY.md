# Reproduce the original PyBot measurements

Default PyJev inference does not require Git, Docker, NumPy or network access. This page is for reproducing the **additional external comparator**, not for using PyJev. Run the commands from a checkout of this project.

1. Obtain a clean checkout of [huggingface/pybot at the fixed commit](https://github.com/huggingface/pybot/tree/7d63c7fbebb44c7e466e5c8b5c1f341ab767929e) and the [two pinned JSONL files](README.md). Keep them outside this repository. The comparison checks the full model-source fingerprint and both dataset hashes. Do not use production/customer data or run code from a dataset.
2. Use a trusted **local** Docker daemon with at least 4 GiB available to the container. Pull the official pinned Python image in advance. Inference then uses no network and does not mount your home, SSH credentials or Docker socket. The registered protocol bytes are mounted at the adapter's original read-only path; the English reading copy is not used for hashing. Only the project modules, upstream source and pinned corpus files are mounted read-only.
3. Run task-directed and verbatim conditions separately. The wrapper requires new output filenames. Original free-form replies are not saved or printed.

~~~bash
git clone https://github.com/huggingface/pybot.git /path/to/original-pybot
git -C /path/to/original-pybot switch --detach 7d63c7fbebb44c7e466e5c8b5c1f341ab767929e
docker pull python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535
python -m research.run_original --upstream /path/to/original-pybot --external /path/to/translation-cases.jsonl --legacy /path/to/zh-ipi-v3.jsonl --mode task --out /tmp/pybot-task-replay.json
python -m research.run_original --upstream /path/to/original-pybot --external /path/to/translation-cases.jsonl --legacy /path/to/zh-ipi-v3.jsonl --mode raw --out /tmp/pybot-raw-replay.json
~~~

Formal denominators: 2,057 task-directed comparisons (three cohorts); 673 additional verbatim turns (two new cohorts). Turn wall time, platform and timeouts may differ on a different machine. Input preparation and the neutral parity probe are not scored examples. The original runtime swallows some internal exceptions into an ordinary fallback reply as its native one-shot CLI does; a nonlabel includes such free replies and is not proof that no internal exceptions occurred. Compare the resulting aggregate JSON with the [release report](../docs/comparison.md).
