"""Only this standalone stage joins sealed labels with fixed predictions; aggregates only."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from .common import HERE, filehash, jsonl, save_json
MODES=("pyjev","hikma_050","hikma_0005","pyjev_shadow")

def decisions(r):
    if r["pyjev"] not in ("review","no_signal","incomplete") or r["shadow"] not in ("review","record_only","no_signal","incomplete"):
        raise ValueError("invalid PyJev route")
    p=r["p"]
    if not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1:
        raise ValueError("bad model score")
    return (None if r["pyjev"]=="incomplete" else int(r["pyjev"]=="review"),
            int(p>=.5), int(p>=.005),
            None if r["shadow"]=="incomplete" else int(r["shadow"]=="review"))

def evaluate(golds, predictions):
    pk={p["id"]:p for p in predictions}
    if len(pk)!=len(predictions) or len({g["id"] for g in golds})!=len(golds) or {g["id"] for g in golds}!=set(pk):
        raise ValueError("not a complete unique paired cohort")
    result={}
    for gold in golds:
        y=gold["label"]
        if type(y) is not int or y not in (0,1): raise ValueError("not binary gold")
        pred=decisions(pk[gold["id"]])
        for group in ["all",*gold["strata"]]:
            t=result.setdefault(group, dict(n=0,positive=0,negative=0,
                modes={m:dict(tp=0,fp=0,fn=0,tn=0,missing_pos=0,missing_neg=0) for m in MODES},
                paired={v:{k:0 for k in ("neither_wrong","only_pyjev_wrong","only_hikma_wrong","both_wrong","incomplete")}
                        for v in ("positive","negative")}))
            truth="positive" if y else "negative"
            t["n"]+=1;t[truth]+=1
            for mode,v in zip(MODES,pred):
                key=(("missing_pos" if y else "missing_neg") if v is None else
                     ("tp" if v else "fn") if y else ("fp" if v else "tn"))
                t["modes"][mode][key]+=1
            a,b=pred[:2]
            key=("incomplete" if a is None or b is None else
                 ("neither_wrong","only_hikma_wrong","only_pyjev_wrong","both_wrong")[2*int(a!=y)+int(b!=y)])
            t["paired"][truth][key]+=1
    for row in result.values():
        for m in row["modes"].values():
            if m["tp"]+m["fn"]+m["missing_pos"]!=row["positive"] or m["tn"]+m["fp"]+m["missing_neg"]!=row["negative"]:
                raise ValueError("accounting mismatch")
        for y in ("positive","negative"):
            if sum(row["paired"][y].values())!=row[y]: raise ValueError("pair accounting")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gold",type=Path,required=True);p.add_argument("--predictions",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();seal=json.loads((HERE/"cohort.json").read_text());rec=json.loads(a.receipt.read_text())
    if (filehash(a.gold)!=seal["gold_sha256"] or filehash(a.predictions)!=rec["predictions_sha256"] or
            rec["inputs_sha256"]!=seal["inputs_sha256"] or rec["rows"]!=seal["retained_rows"]):
        raise ValueError("seal mismatch")
    groups=evaluate(list(jsonl(a.gold)), list(jsonl(a.predictions)))
    if groups["all"]["n"]!=rec["rows"] or {k:v["n"] for k,v in groups.items() if k!="all"}!=seal["strata"]:
        raise ValueError("wrong cohort/group totals")
    save_json(a.out,dict(schema=1,receipt=rec,groups=groups))

if __name__=="__main__":
    main()
