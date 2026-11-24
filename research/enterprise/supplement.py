"""Registered negative controls from real public software release notes. No network in inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from .common import HERE, filehash, jsonl, save_json, save_rows
from .prepare import histories, item, overlap
from .score import evaluate

SOURCES=json.loads((HERE/"org-sources.json").read_text())
HEADING=re.compile(r"^## (?!#).*?(?<![\d.])(\d+\.\d+\.\d+)(?![\w.+-])")
DATE=re.compile(r"`(2026-\d{2}-\d{2})`")

def sections(text):
    current=None
    for line in text.splitlines():
        if line.startswith("## "):
            if current:yield current
            m=HEADING.match(line)
            current=[m[1],[line],[]] if m else None
            continue
        if current:
            current[1].append(line)
            if re.match(r"^\s*[-*] ",line) and len(re.findall(r"[\u3400-\u9fff]",line))>=8:
                current[2].append(line)
    if current:yield current

def select(data):
    xs=[]; inventory={}
    for file,spec in SOURCES.items():
        path=data/file
        if filehash(path)!=spec["sha256"]:raise ValueError("release-notes hash mismatch")
        src=file[:-3];versions=[];n=0
        for ver,lines,bullets in sections(path.read_text(encoding="utf8")):
            m=DATE.search("\n".join(lines[:5]))
            if not m or not ("2026-05-01"<=m[1]<="2026-11-17") or not bullets:continue
            if ver in versions:raise ValueError("duplicate release")
            versions.append(ver)
            for pos in ([0,-1] if len(bullets)>1 else [0]):
                xs.append(item(src,ver+":"+str(pos),bullets[pos],0,[src]));n+=1
            if len(versions)==12:break
        inventory[src]={"versions":versions,"candidates":n}
    return xs,inventory

def prepare(a):
    if filehash(a.primary_inputs)!=json.loads((HERE/"cohort.json").read_text())["inputs_sha256"]:
        raise ValueError("primary inputs mismatch")
    xs,inv=select(a.data)
    def refs():
        yield from histories(a.data,a.prior_dir or a.data,a.business_fixture)
        yield "earlier455",(x["text"] for x in jsonl(a.primary_inputs))
    keep,audit=overlap(xs,refs())
    rows=sorted((xs[i] for i in keep),key=lambda r:r["id"])
    a.out.mkdir(parents=True,exist_ok=True)
    inputs=a.out/"inputs.jsonl";g=a.out/"gold.jsonl"
    save_rows(inputs,({"id":r["id"],"text":r["text"]} for r in rows))
    save_rows(g,({k:v for k,v in r.items() if k!="text"} for r in rows))
    save_json(a.out/"org-cohort.json",dict(inventory=inv,rows=len(rows),overlap=audit,
               inputs_sha256=filehash(inputs),gold_sha256=filehash(g)))
    print("retained release-note controls:",len(rows))

def infer(a):
    from .infer import Comparator
    from pyjev import Auditor
    cohort=json.loads((HERE/"org-cohort.json").read_text())
    if filehash(a.inputs)!=cohort["inputs_sha256"]:raise ValueError("unsealed controls")
    py=Auditor();net=Comparator(a.data);rows=[]
    for r in jsonl(a.inputs):
        if set(r)!={"id","text"}:raise ValueError("unexpected fields")
        y=py.audit(r["text"]);p,w,n=net.predict(r["text"])
        rows.append(dict(id=r["id"],pyjev=y.review,shadow=y.experimental_review,p=p,windows=w,tokens=n))
    if len(rows)!=cohort["rows"]:raise ValueError("missing controls")
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/"predictions.jsonl";save_rows(path,rows)
    receipt=dict(rows=len(rows),inputs_sha256=filehash(a.inputs),predictions_sha256=filehash(path),
                 windows=sum(x["windows"] for x in rows))
    save_json(a.out/"org-prediction-receipt.json",receipt)
    print("sealed predictions:",receipt["predictions_sha256"])

def score(a):
    c=json.loads((HERE/"org-cohort.json").read_text());rec=json.loads(a.receipt.read_text())
    if filehash(a.gold)!=c["gold_sha256"] or rec["inputs_sha256"]!=c["inputs_sha256"] or filehash(a.predictions)!=rec["predictions_sha256"]:
        raise ValueError("labels/predictions do not match the seals")
    groups=evaluate(list(jsonl(a.gold)),list(jsonl(a.predictions)))
    if groups["all"]["n"]!=c["rows"] or groups["all"]["positive"]!=0:raise ValueError("control scope")
    save_json(a.out,dict(receipt=rec,groups=groups))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="op",required=True)
    def opt(p,n,req=True):p.add_argument("--"+n,type=Path,required=req)
    f=sub.add_parser("fetch");opt(f,"out")
    b=sub.add_parser("prepare");opt(b,"data");opt(b,"primary-inputs");opt(b,"out");opt(b,"prior-dir",False);opt(b,"business-fixture",False)
    i=sub.add_parser("infer");opt(i,"data");opt(i,"inputs");opt(i,"out")
    s=sub.add_parser("score");opt(s,"gold");opt(s,"predictions");opt(s,"receipt");opt(s,"out")
    a=p.parse_args()
    if a.op=="fetch":
        from .fetch import fetch
        a.out.mkdir(parents=True,exist_ok=True)
        for n,v in SOURCES.items():fetch(a.out,n,v)
    else:{"prepare":prepare,"infer":infer,"score":score}[a.op](a)
