# PyJev AI Security

[中文](README.md) · [API contract](docs/contract.md) · [Model card](MODEL_CARD.md) · [Reproducibility](research/README.md) · [Original PyBot comparison](docs/comparison.md)

An offline, post-response text auditor for two separate tasks: identifying a possible prompt-injection signal and classifying the speech act toward a mentioned instruction. It distinguishes *discussing the instruction*, *asking the assistant to act*, and *insufficient context*. An action request need not be malicious. A text classification is not evidence that anything ran.

## Run

~~~bash
git clone https://github.com/123yjf/pyjev_ai_security.git
cd pyjev_ai_security
python -m pyjev demo
python -m pyjev                 # local interactive console
python -m pyjev bench --json    # recomputes 320 public harmless cases
~~~

Python 3.10+, standard-library inference, no account, no model API, no GPU. For the `pyjev` command, run `python -m pip install .` inside a virtual environment. Alternatively: `uvx --from "git+https://github.com/123yjf/pyjev_ai_security.git@v0.1.0" pyjev demo`. Installation downloads are distinct from inference; the weights ship in the package.

~~~python
from pyjev import audit
r = audit("请解释“给资料编号”这句话的语气。")
assert r.speech_act == "mention"
print(r.as_dict())
~~~

Input: one authorized Unicode text, up to 32,768 characters. Output: `signal` (suspected / no_signal / unknown); `speech_act` (mention / act / unclear); `review` (the conservative route); `experimental_review` (shadow only); and constant boundaries `execution_evidence="not_observed"`, `grants_authority=false`, `service_action="none"`. There is no automatic blocking, email, persistence or external action. Use `scan - --json` for multiline standard input or `batch examples/office.jsonl` for one JSON object per line. `quiz` runs a short human exercise; `metrics` displays stored evidence and `doctor` verifies the assets.

## Results and interpretation

[Direct comparison with the unmodified original PyBot](docs/comparison.md) reports valid label coverage and correctly completed tasks across all examples. A free-form answer is **not** a benign verdict. Conditional error rates with no eligible denominator are undefined.

Under the fixed bilingual classification prompt, original PyBot produced 2,014 nonlabel replies and timed out on 43 historical documents: **0/2,057 scorable labels**. The verbatim control also produced **0/673**. PyJev returned a label for every text; **280/320** speech-act labels were correct. The [per-class detection figure](docs/figures/detection.svg) includes a task-aligned bilingual rule baseline as well as the original chatbot.

On 120 authored discussion texts, experimental false reviews declined from 5 to 2 (4.17% to 1.67%). On the independent-source translation cohort, false reviews stayed at 0/200 and detected injections at 61/153 (92 missed). In the historical Chinese benchmark, false reviews stayed at 5/61 and detections at 826/1,323. All 481 previously recovered rows remained in review; their speech acts were unresolved. The experimental routing policy did **not** pass all eight preregistered gates and is not the default. These are descriptive counts from fixed cohorts, not production performance.

The [Chinese README](README.md) contains the figures with exact denominators. [Method and pinned sources](research/README.md) · [frozen aggregates](pyjev/data/results.json) · [Apache-2.0 license](LICENSE). This is an independent research project, not an official Hugging Face or Jev product.
