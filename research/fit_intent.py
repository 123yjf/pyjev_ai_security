"""Refit only the speech-act head on the 225 authored lessons; never reads examination text.
Optional NumPy dependency. This does not train the earlier bilingual signal detector.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","VECLIB_MAXIMUM_THREADS","MKL_NUM_THREADS"):os.environ[k]="1"
import numpy as np
from pyjev._intent import LABELS,THRESHOLDS,Head,frame,feats,adjudicate
from research.curriculum import lessons

def require(ok,msg):
    if not ok: raise ValueError(msg)
def js(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False)

def probs(z):
    s=np.exp(z-z.max(1,keepdims=True));return s/s.sum(1,keepdims=True)

def fit(bags,labels,fitidx):
    df=Counter(k for i in fitidx for k in bags[i]);keys=sorted(k for k in df if df[k]>=2)
    ids={k:j for j,k in enumerate(keys)};idf=np.array([1+math.log((1+len(fitidx))/(1+df[k])) for k in keys])
    X=np.zeros((len(labels),len(keys)))
    for j,bag in enumerate(bags):
        for k,v in bag.items():
            if k in ids:X[j,ids[k]]=v*idf[ids[k]]
    X/=np.maximum(np.sqrt((X*X).sum(1,keepdims=True)),1e-20)
    A=X[fitidx];y=labels[fitidx];one=np.eye(3)[y];a=1/(3*np.bincount(y)[y]);w=np.zeros((len(keys),3));b=np.zeros(3)
    hist={};changes=0;lam=.0009
    for i in range(1,1001):
        p=probs(A@w+b);delta=(p-one)*a[:,None];dw=A.T@delta+lam*w;db=delta.sum(0)
        require(np.isfinite(dw).all() and np.isfinite(db).all(),"gradient")
        nw=w-2*dw;b-=2*db;changes+=int(np.any(nw!=w));w=nw
        if i in (1,100,500,1000):
            pp=probs(A@w+b);hist[str(i)]=round(float(-(a*np.log(pp[np.arange(len(y)),y])).sum()+lam*(w*w).sum()/2),9)
    require(changes==1000,"no-op training")
    return probs(X@w+b),keys,idf,w,b,dict(updates=changes,fit_rows=len(y),features=len(keys),loss_after=hist)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,help="optional NEW file for weights; existing files are never replaced")
    args=parser.parse_args(argv)
    if args.out and args.out.exists():parser.error("output file already exists")
    rows=list(lessons());frames=[frame(r[0]) for r in rows];bags=[feats(f) for f in frames]
    y=np.array([LABELS.index(r[1]) for r in rows]);oof=np.full((len(rows),3),np.nan)
    for fold in range(5):
        dev=[i for i,r in enumerate(rows) if r[2]==fold];tr=[i for i,r in enumerate(rows) if r[2]!=fold]
        pred,*_=fit(bags,y,tr);oof[dev]=pred[dev]
    require(np.isfinite(oof).all(),"incomplete OOF");valid=[]
    for tau in THRESHOLDS:
        cm=[[0,0,0] for _ in LABELS]
        for f,g,p in zip(frames,y,oof): cm[g][LABELS.index(adjudicate(f,p,tau))]+=1
        if cm[1][0]+cm[2][0]==0 and cm[0][0]>0:valid.append((cm[0][0],tau))
    tau=max(valid)[1] if valid else None
    pred,keys,idf,w,b,stats=fit(bags,y,list(range(len(y))))
    meta=dict(format="nuwa-mention-head-v1",classes=LABELS,tau=tau,bias=b.tolist())
    triples=[[k,float(i),v.tolist()] for k,i,v in zip(keys,idf,w)]
    model=Head(dict(**meta,features=triples))
    require(all(model.state(r[0])==adjudicate(f,p,tau) for r,f,p in zip(rows,frames,pred)),"prediction parity")
    blob=(js(meta)[:-1]+',"features":[\n'+",\n".join(js(t) for t in triples)+"\n]}\n").encode()
    h=hashlib.sha256(blob).hexdigest()
    if args.out:
        with args.out.open("xb") as f: f.write(blob)
    print(js(dict(rows=len(rows),folds=5,updates_per_fit=stats["updates"],selected_threshold=tau,sha256=h,
        bitwise_matches_release=h=="9bbc915995945b5cbf3f4e2f9ef35254ac00e331b1896e2ebf15a27e84661ded",
        note="Floating-point bytes may differ across BLAS/NumPy builds. No evaluation text used.")))
    return 0
if __name__=="__main__":raise SystemExit(main())
