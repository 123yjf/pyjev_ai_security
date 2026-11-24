"""Local read-only paired inference. The formal runner has no argument for gold labels."""
import argparse
from collections import Counter
from importlib.metadata import version
import json
import math
from pathlib import Path
import statistics
from .common import HERE, checked, digest, filehash, jsonl, save_json, save_rows, wire

def windows(ids, body=510, overlap=64):
    if not 0 <= overlap < body:
        raise ValueError("invalid overlap")
    start = 0
    while True:
        yield ids[start:start+body]
        if start+body >= len(ids):
            break
        start += body-overlap

class Comparator:
    def __init__(self, root):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.tok=Tokenizer.from_file(str(checked(root, "tokenizer.json")))
        self.tok.no_truncation(); self.tok.no_padding()
        if self.tok.encode("").ids != [1,2] or self.tok.token_to_id("[PAD]") != 0:
            raise ValueError("tokenizer special IDs changed")
        opts=ort.SessionOptions(); opts.intra_op_num_threads=2; opts.inter_op_num_threads=1
        self.net=ort.InferenceSession(str(checked(root,"detector.onnx")),sess_options=opts,
                                      providers=["CPUExecutionProvider"])
        if [i.name for i in self.net.get_inputs()]!=["input_ids","attention_mask"] or self.net.get_outputs()[0].name!="logits":
            raise ValueError("wrong export signature")

    def predict(self, text):
        import numpy as np
        ids=self.tok.encode(text,add_special_tokens=False).ids
        scores=[]
        for piece in windows(ids):
            x=np.array([[1,*piece,2]],dtype=np.int64)
            raw=self.net.run(["logits"],{"input_ids":x,"attention_mask":np.ones_like(x)})[0]
            if raw.shape!=(1,2) or not np.isfinite(raw).all():
                raise ValueError("invalid model output")
            e=np.exp(raw[0].astype(np.float64)-np.max(raw[0]))
            scores.append(float(e[1]/e.sum()))
        return max(scores), len(scores), len(ids)

def polarity(root, out):
    cmp=Comparator(root)
    bins={0:[],1:[]}
    for row in jsonl(checked(root,"h-test.jsonl")):
        if row["metadata"]["language"]=="en":
            bins[row["label"]].append(row["text"])
    summary={}
    for y in (0,1):
        xs=sorted(set(bins[y]),key=lambda x:digest(x.encode()))[:16]
        if len(xs)!=16: raise ValueError("too few legacy direction controls")
        ps=[cmp.predict(x)[0] for x in xs]
        summary[str(y)]={"n":len(ps),"median_class1_probability":statistics.median(ps),
                         "class1_at_half":sum(p>=.5 for p in ps)}
    if not summary["0"]["median_class1_probability"] < .5 < summary["1"]["median_class1_probability"]:
        raise ValueError("legacy positive-column check failed; do not score holdout")
    save_json(out,summary)
    print(wire(summary))

def run(data, inputs, out):
    from pyjev import Auditor
    seal=json.loads((HERE/"cohort.json").read_text())
    if filehash(inputs)!=seal["inputs_sha256"]: raise ValueError("unsealed inputs")
    model=Comparator(data); py=Auditor()
    counts=Counter(); acc=[]; seen=set(); prev=""
    for row in jsonl(inputs):
        if set(row)!={"id","text"} or row["id"]<=prev or row["id"] in seen:
            raise ValueError("blinded input schema or order")
        prev=row["id"]; seen.add(prev)
        y=py.audit(row["text"])
        p,w,n=model.predict(row["text"])
        acc.append(dict(id=prev,pyjev=y.review,shadow=y.experimental_review,p=p,windows=w,tokens=n))
        counts["rows"]+=1; counts["windows"]+=w
        if len(seen)%100==0:print("blind inference:",len(seen),"texts",flush=True)
    if len(seen)!=seal["retained_rows"]:raise ValueError("incomplete inference")
    out.mkdir(parents=True,exist_ok=True); trace=out/"predictions.jsonl"
    save_rows(trace,acc)
    receipt=dict(schema=1,predictions_sha256=filehash(trace),inputs_sha256=filehash(inputs),
                 rows=len(seen),windows=counts["windows"], multiwindow=sum(v["windows"]>1 for v in acc),
                 max_windows=max(v["windows"] for v in acc),max_tokens=max(v["tokens"] for v in acc),
                 versions={p:version(p) for p in ("numpy","onnxruntime","tokenizers")},provider="CPUExecutionProvider")
    save_json(out/"prediction-receipt.json",receipt)
    print(wire(receipt))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--data",type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--inputs",type=Path); group.add_argument("--polarity",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.polarity:polarity(a.data,a.out)
    else:run(a.data,a.inputs,a.out)
