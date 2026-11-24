"""Label-free offline inference; no network, gold argument, tool, execution or I/O trace content."""
import argparse,json
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from research.enterprise.infer import Comparator
from research.enterprise.common import HIKMA,PYJEV,jsonl,save_rows,save_json,filehash
from pyjev import Auditor
from pyjev_v1 import Auditor as V1Auditor
from . import __file__ as root_file

def run(data,inputs,out):
    seal=json.loads((Path(root_file).parent/"cohort.json").read_text())
    if filehash(inputs)!=seal["inputs_sha256"]:raise ValueError("unknown inputs")
    baseline=Auditor();scope=V1Auditor();hikma=Comparator(data);rows=[];prev="";windows=0
    for v in jsonl(inputs):
        if set(v)!={"id","text"} or v["id"]<=prev:raise ValueError("schema or order")
        prev=v["id"];a=baseline.audit(v["text"]);b=scope.audit(v["text"]);p,w,n=hikma.predict(v["text"])
        assert a.signal==b.original_signal and a.review==b.original_review
        rows.append(dict(id=prev,base=a.review,base_speech=a.speech_act,scope=b.route,scope_raw=b.signal,
                         scope_speech=b.speech_act,review=b.needs_review,p=p,windows=w,tokens=n))
        windows+=w
        if len(rows)%150==0:print("blinded inputs:",len(rows),flush=True)
    if len(rows)!=seal["retained"]:raise ValueError("incomplete inference")
    out.mkdir(exist_ok=False);trace=out/"predictions.jsonl";save_rows(trace,rows)
    rec=dict(candidate_commit=seal["candidate_commit"],baseline=PYJEV,hikma=HIKMA,provider="CPUExecutionProvider",
             versions={k:version(k) for k in ("numpy","onnxruntime","tokenizers")},rows=len(rows),windows=windows,
             multiwindow=sum(r["windows"]>1 for r in rows),max_windows=max(r["windows"] for r in rows),
             max_tokens=max(r["tokens"] for r in rows),inputs_sha256=seal["inputs_sha256"],predictions_sha256=filehash(trace))
    save_json(out/"prediction-receipt.json",rec);print("frozen predictions:",len(rows),rec["predictions_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("data","inputs","out"):p.add_argument("--"+n,required=True,type=Path)
    run(**vars(p.parse_args()))
