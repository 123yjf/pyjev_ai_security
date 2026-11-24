"""Same-text framing control for the two new cohorts, not a new labeler."""
import argparse
from collections import Counter
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
from research import compare_pybot as c

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--pybot",type=Path,required=True)
    p.add_argument("--external",type=Path,required=True);p.add_argument("--legacy",type=Path,required=True,help="locked data verifier input; historical suite is not scored here")
    p.add_argument("--jobs",type=int,default=2,choices=range(1,9));a=p.parse_args()
    if os.environ.get("PYTHONHASHSEED")!="0" or "fork" not in mp.get_all_start_methods():p.error("requires POSIX fork and PYTHONHASHSEED=0")
    ds=c.cohort_inputs(a.external,a.legacy);del ds["legacy"]
    c.ORIGINAL,c.RUNTIME,c.INITIAL=c.load_upstream(a.pybot.resolve());c.TASK={"office":"","binary":""}
    labels={s:tuple(c.MAP["office" if s=="office" else "binary"]) for s in ds}
    cms={s:{g:Counter() for g in lab} for s,lab in labels.items()};seen=set()
    items=[(s,i,t) for s,rows in ds.items() for i,(t,_) in enumerate(rows)]
    with mp.get_context("fork").Pool(a.jobs,maxtasksperchild=1) as pool:
        for s,i,v in pool.imap_unordered(c.worker,items,chunksize=1):
            if (s,i) in seen:raise ValueError("duplicate item")
            seen.add((s,i));cms[s][ds[s][i][1]][v]+=1
            if len(seen)%100==0:print(f"raw-control completed {len(seen)}/{len(items)}",file=sys.stderr,flush=True)
    if len(seen)!=673:raise ValueError("missing item")
    print(json.dumps(dict(format="pyjev-original-pybot-raw-v1",pybot_commit=c.REV,n=len(seen),raw_texts_exported=0,
       protocol_sha256=c.digest(Path(__file__).with_name("PYBOT_RAW_CONTROL.md").read_bytes()),
       adapter_sha256=c.digest(Path(__file__).read_bytes()),system={s:c.summarize(cms[s],labels[s]) for s in ds}),sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
