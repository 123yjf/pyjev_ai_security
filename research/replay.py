"""Reproduce aggregate public benchmark counts against immutable data. No fetch or execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from pyjev import Auditor
from pyjev.api import _models, _read

SOURCES = {
    "external": ("e3497d7e7e68288059358d1c8cea606635b6ab6b8e2accd94cddfae78e7f1caf", 2_000_000),
    "legacy": ("a6c9e50792b415d8cf1479b7873f9cceb36792ab701df2f92c1655a6450d1f48", 2_100_000),
}
def sha(b):return hashlib.sha256(b).hexdigest()
def cohort(ids):
    return sha(json.dumps(sorted(sha(str(i).encode()) for i in ids),separators=(",",":")).encode())

def replay(kind, content):
    digest,limit = SOURCES[kind]
    if len(content)>limit or sha(content)!=digest: raise ValueError("file size or SHA-256 mismatch")
    a=Auditor(); base,_=_models(); frozen=_read("results.json"); seen=set(); added=[]; retained=[]
    tp=fp=before_tp=before_fp=negative=positive=0
    for line in content.splitlines():
        d=json.loads(line)
        if kind=="legacy" and d["language"]!="zh": continue
        text=d["text"]
        if kind=="legacy": gold=d["label"]=="injected"; ident=d["sample_id"]
        else: gold=int(d["label"])==1; ident=d["id"]
        if ident in seen: raise ValueError("duplicate input id")
        seen.add(ident);r=a.audit(text);raw=r.signal=="suspected";review=r.experimental_review=="review"
        if r.signal=="unknown": raise ValueError("unexpected incomplete sample")
        if gold:
            positive+=1;before_tp+=raw;tp+=review
            if kind=="legacy" and raw and not base.evidence(text)[0]:
                added.append(ident)
                if review: retained.append(ident)
        else:negative+=1;before_fp+=raw;fp+=review
    row=frozen["old_chinese"]["comparison"] if kind=="legacy" else frozen["new_external"]["full"]
    expected=(row["raw"]["tp"],row["raw"]["fp"],row["review"]["tp"],row["review"]["fp"],row["raw"]["fn"],row["raw"]["tn"])
    ok=(before_tp,before_fp,tp,fp,positive-before_tp,negative-before_fp)==expected
    out=dict(suite=kind,texts=len(seen),normal=negative,injections=positive,false_reviews_before=before_fp,
             false_reviews_experimental=fp,detected_before=before_tp,detected_experimental=tp,missed=positive-tp)
    if kind=="legacy":
        z=frozen["old_chinese"]["protected_481"]
        ok=ok and cohort(added)==z["ids_sha256"] and cohort(retained)==z["review_ids_sha256"]
        out.update(previously_recovered=len(added),still_reviewed=len(retained),protected_sets_match=cohort(added)==cohort(retained))
    return dict(**out,matches_frozen_evidence=ok)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("suite",choices=SOURCES);p.add_argument("file",help="pinned JSONL filename, or - for stdin");args=p.parse_args(argv)
    try:
        n=SOURCES[args.suite][1]+1
        if args.file=="-": data=sys.stdin.buffer.read(n)
        else:
            with Path(args.file).open("rb") as f:data=f.read(n)
        out=replay(args.suite,data)
    except (OSError,ValueError,KeyError):
        print("Could not verify pinned input; no benchmark score reported.",file=sys.stderr);return 2
    print(json.dumps(out,sort_keys=True));return 0 if out["matches_frozen_evidence"] else 1
if __name__=="__main__":raise SystemExit(main())
