"""Generate the public baseline report from verified counts; use --check to detect drift."""
import argparse
import hashlib
from pathlib import Path
from pyjev.api import _read
from pyjev.comparison import measured,SETTINGS,SUITES
here=Path(__file__).resolve().parent
NAMES = {"office":"Office intent", "external":"Translated scenarios", "legacy":"Historical Chinese documents"}
SYSTEM = {"pyjev":"Historical native interface", "pybot_task":"Original PyBot: prompted", "pybot_raw":"Original PyBot: verbatim"}

def ratio(x, n):
    return f"{x:,}/{n:,} ({100*x/n:.1f}%)" if n else "Not scorable"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def render():
    scores=measured()
    a,b=_read("pybot-comparison.json"),_read("pybot-raw-control.json")
    for record, protocol, adapter in ((a,"fixtures/pybot-protocol-registered.utf8","compare_pybot.py"),(b,"PYBOT_RAW_CONTROL.md","raw_control.py")):
        if record["protocol_sha256"] != digest(here/protocol) or record["adapter_sha256"] != digest(here/adapter):
            raise ValueError("Scoring protocol drift")
    prompted, raw = scores["pybot_task"], scores["pybot_raw"]
    n=sum(x["n"] for x in prompted.values()); nr=sum(x["n"] for x in raw.values())
    valid=sum(x["valid"] for x in prompted.values()); vr=sum(x["valid"] for x in raw.values())
    lines=["# Historical control: original PyBot", "",
           "This is an interface comparison, not the current specialist benchmark. Could an unmodified general-purpose chatbot return the labels required for a review queue? The scoring adapter does not infer verdicts from free-form replies.", "",
           f"The [pinned original implementation](https://github.com/huggingface/pybot/tree/{a['pybot_commit']}) returned scorable labels on **{valid:,}/{n:,}** task-prompt inputs and **{vr:,}/{nr:,}** verbatim inputs. Texts overlap across these settings; do not add them as unique cases. No label is not a correct negative.", "",
           "| Dataset | Interface | Scorable / all | Correct / all | Accuracy among scorable | No label / timeout / error |",
           "|---|---|---:|---:|---:|---:|"]
    for suite in SUITES:
        for engine in SETTINGS:
            row=scores[engine].get(suite)
            if row:
                lines.append(f"| {NAMES[suite]} | {SYSTEM[engine]} | {ratio(row['valid'],row['n'])} | {ratio(row['correct'],row['n'])} | {ratio(row['correct'],row['valid'])} | {row['no_label']} / {row['timeout']} / {row['error']} |")
    lines += ["", "A valid indeterminate intent is a semantic answer. A non-label is not. These known suites were used to compare output contracts, not to establish fresh generalization or safety.", "",
              "## Injection detection and false alarms", "",
              "| Corpus | Interface | False alarms / scorable negatives | Detections / scorable positives |", "|---|---|---:|---:|"]
    for suite in ("external","legacy"):
        for engine in SETTINGS:
            row=scores[engine].get(suite)
            if row:
                lines.append(f"| {NAMES[suite]} | {SYSTEM[engine]} | {ratio(row['false_positives'],row['valid_normals'])} | {ratio(row['true_positives'],row['valid_positives'])} |")
    lines+=["","An empty denominator is unscorable, not zero. These historical native results are not measurements of pyjev_v1.",
            "", "[Output coverage](figures/baselines.svg) · [Injection detection](figures/detection.svg) · [Intent](figures/intent.svg) · [False reviews](figures/false-reviews.svg)",
            "", "[Frozen counts](../pyjev/data/pybot-comparison.json) · [Verbatim control](../pyjev/data/pybot-raw-control.json) · [Offline replay](../research/BASELINE_REPLAY.md) · [Current paired study](audit-study.md)", ""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--check",action="store_true");a=p.parse_args();out=render()
    if a.check:
        if out!=(here.parent/"docs/comparison.md").read_text():raise SystemExit("comparison report is stale")
    else:print(out,end="")
if __name__=="__main__":main()
