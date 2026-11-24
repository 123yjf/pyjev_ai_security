"""Archived sets are checks only. No challenge examples or row-level decisions leave the machine."""
import argparse
from pathlib import Path
from collections import Counter
from pyjev import Auditor
from pyjev.api import _models,_read
from pyjev._office import exam
from research.replay import SOURCES,cohort
from research.enterprise.common import jsonl,filehash,save_json
from .score import HERE,binary,checked_join,read
from candidates.scope1 import ScopeAuditor

def run(old,prior,output):
    candidate=ScopeAuditor();emb,_=_models();out={};frozen=HERE.parent/"enterprise"
    for sub,basepath,pref in [("seal","pred",""),("orgseal","orgpred","org-")]:
        seal=read(frozen/(pref+"cohort.json")); rec=read(frozen/(pref+"prediction-receipt.json"))
        inp=old/sub/"inputs.jsonl"
        assert filehash(inp)==seal["inputs_sha256"]
        olds=checked_join(old/sub/"gold.jsonl",old/basepath/"predictions.jsonl",seal,rec);rows=[]
        for x,g in zip(jsonl(inp),olds):
            assert x["id"]==g["id"]
            d=candidate.audit(x["text"]);assert d.original_review==g["pyjev"]
            rows.append({**g,"base":d.original_review,"review":d.needs_review,"scope":d.route})
        for s in (("all455","agent","mention_or_quote","business_docs","risk_discussion","quoted_design") if sub=="seal" else ("org47",)):
            out[s]=binary(rows if s in ("all455","org47") else [r for r in rows if s in r["strata"]])
    for key,(sha,_) in SOURCES.items():
        src=prior/(key+".jsonl");assert filehash(src)==sha; c=Counter();protected=[];kept=[];raw_kept=0
        for r in jsonl(src):
            if key=="legacy" and r["language"]!="zh":continue
            pos=(r["label"]=="injected") if key=="legacy" else r["label"]==1
            d=candidate.audit(r["text"]);a=d.original_review=="review";b=d.needs_review
            if b is None:raise ValueError("unexpected abstention in archive")
            c["rows"]+=1;c["positive"]+=pos;c["negative"]+=not pos
            for k,p in (("base",a),("scope",b)):
                cell=("tp" if p else "fn") if pos else ("fp" if p else "tn")
                c[k+"_"+cell]+=1
            c["tp_lost"]+=int(pos and a and not b);c["tp_gained"]+=int(pos and not a and b)
            if key=="legacy" and pos and d.original_signal=="suspected" and not emb.evidence(r["text"])[0]:
                protected.append(r["sample_id"])
                if b:kept.append(r["sample_id"])
                raw_kept+=d.signal=="suspected"
        out[key]=dict(c)
        if key=="legacy":
            h=cohort(protected);assert len(protected)==481 and h==_read("results.json")["old_chinese"]["protected_481"]["ids_sha256"]
            out["protected_481"]=dict(total=len(protected),effective_kept=len(kept),raw_kept=raw_kept,
                                      missing=len(protected)-len(kept),cohort_sha256=h,kept_set_sha256=cohort(kept))
    office={};original=Auditor()
    for text,y,_ in exam():
        d=candidate.audit(text);base=original.audit(text)
        x=office.setdefault(y,Counter());x["rows"]+=1;x["scope_correct"]+=d.speech_act==y;x["base_correct"]+=base.speech_act==y
        x["previous_correct_lost"]+=(base.speech_act==y and d.speech_act!=y)
        x["previous_wrong_recovered"]+=(base.speech_act!=y and d.speech_act==y)
    out["office320"]=office
    save_json(output,out)
    for k in ("all455","agent","mention_or_quote","org47"):
        d=out[k];print(k,d["positive"],d["negative"],[(m,d["modes"][m]["fn"],d["modes"][m]["fp"]) for m in ("v010","scope")],d["paired"])
    print("protected:",out["protected_481"]["effective_kept"],"legacy:",out["legacy"],"external:",out["external"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for n in ("old","prior","output"):p.add_argument("--"+n,type=Path,required=True)
    run(**vars(p.parse_args()))
