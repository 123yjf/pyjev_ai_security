"""Descriptive task-aligned controls, separate from the unmodified original PyBot.
All frozen methods see the same supplied case text; no training, no tuning, no network.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from pyjev import Auditor
from pyjev.api import _models
from research.replay import SOURCES

def compute(path,kind):
    digest,maxbytes=SOURCES[kind]
    with path.open("rb") as f:b=f.read(maxbytes+1)
    if hashlib.sha256(b).hexdigest()!=digest:raise ValueError("dataset checksum mismatch")
    base,_=_models();a=Auditor();names=("source_only_anchor","bilingual_anchor","checkpoint_323","experimental_routing")
    totals={name:Counter() for name in names}
    for line in b.splitlines():
        obj=json.loads(line)
        if kind=="legacy" and obj["language"]!="zh":continue
        t=obj["text"];y=(obj["label"]=="injected") if kind=="legacy" else bool(int(obj["label"]))
        en,bi,_,raw=base.evidence(t);shadow=a.audit(t).experimental_review=="review"
        for name,hit in zip(names,(en,bi,raw,shadow)): totals[name][("tp" if hit else "fn") if y else ("fp" if hit else "tn")]+=1
    return {key:{i:row[i] for i in ("tp","fn","fp","tn")} for key,row in totals.items()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--external",required=True,type=Path);p.add_argument("--legacy",required=True,type=Path);args=p.parse_args()
    print(json.dumps({k:compute(v,k) for k,v in (("external",args.external),("legacy",args.legacy))},sort_keys=True))
if __name__=="__main__":main()
