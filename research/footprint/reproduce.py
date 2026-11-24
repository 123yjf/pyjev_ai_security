"""Rebuild the numeric study in a fresh destination; reuse only SHA-verified source bytes, never prior seals or decisions."""
import argparse
from collections import Counter
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

from research.enterprise import prepare as enterprise
from research.enterprise import supplement
from research.enterprise.common import CATALOG, filehash, save_json
from research.enterprise.fetch import fetch
from research.scope_study import acquire, infer, prepare, score, verification

def materialize(dest, catalog, caches, offline, *, recent):
    dest.mkdir();summary=Counter()
    for name,spec in catalog.items():
        if Path(name).name!=name:raise ValueError("invalid source name")
        target=dest/name
        src=next((p/name for p in caches if (p/name).is_file()),None)
        if src:
            if filehash(src)!=spec["sha256"]:raise ValueError("cache checksum mismatch: "+name)
            # Originals are used read-only. Callers must never modify hard-linked source assets.
            try:os.link(src.resolve(),target)
            except OSError:
                with src.open("rb") as reader,target.open("xb") as writer:shutil.copyfileobj(reader,writer)
            summary["verified_cache"]+=1
        elif offline:raise FileNotFoundError("verified source unavailable in offline mode: "+name)
        elif recent:
            import hashlib
            data=acquire.source_bytes(spec,name.endswith(".article"))
            if hashlib.sha256(data).hexdigest()!=spec["sha256"]:raise ValueError("download changed: "+name)
            with target.open("xb") as f:f.write(data)
            summary["downloaded"]+=1
        else:
            fetch(dest,name,spec);summary["downloaded"]+=1
        if filehash(target)!=spec["sha256"]:raise ValueError("source checksum mismatch: "+name)
    return dict(summary)

def load(p):return json.loads(p.read_text(encoding="utf8"))

def clean_venv():
    return (sys.prefix!=sys.base_prefix and
            "include-system-site-packages = false" in (Path(sys.prefix)/"pyvenv.cfg").read_text().lower())

def replay(out, caches=(), offline=False, timings=False):
    if sys.version_info[:2]!=(3,11) or not clean_venv():
        raise ValueError("use a new CPython 3.11 venv without system-site-packages; see docs/start-local.md")
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    old=out/"previous";data=out/"current";seal=data/"seal";pred=data/"pred"
    previous=materialize(old,{**CATALOG,**supplement.SOURCES},caches,offline,recent=False)
    current=materialize(data,prepare.INDEX,caches,offline,recent=True)
    print("Verified source artifacts:",previous,current,flush=True)
    primary=enterprise.prepare(old,old,None,old/"seal")
    org_args=SimpleNamespace(data=old,primary_inputs=old/"seal"/"inputs.jsonl",prior_dir=old,
                             business_fixture=None,out=old/"orgseal")
    supplement.prepare(org_args)
    org=load(old/"orgseal"/"org-cohort.json")
    for result, name in ((primary, "cohort.json"), (org, "org-cohort.json")):
        reference=load(Path(enterprise.__file__).parent/name)
        if any(result[k]!=reference[k] for k in ("inputs_sha256","gold_sha256")):
            raise ValueError("archived corpus/label drift")
    prepare.prepare(data,old,old,None,seal)
    new=load(seal/"cohort.json");frozen=load(prepare.HERE/"cohort.json")
    if any(new[k]!=frozen[k] for k in ("inputs_sha256","gold_sha256","retained","kinds")):
        raise ValueError("held-out inputs, labels or counts changed")
    infer.run(old,seal/"inputs.jsonl",pred)
    receipt=load(pred/"prediction-receipt.json");official=load(prepare.HERE/"prediction-receipt.json")
    local=out/"local-tallies.json"
    score.score(seal/"gold.jsonl",pred/"predictions.jsonl",local,pred/"prediction-receipt.json")
    if load(local)!=load(prepare.HERE/"blind-results.json"):raise ValueError("local aggregate discrepancy")
    exact=receipt["predictions_sha256"]==official["predictions_sha256"]
    if exact:verification.verify(data,seal,pred/"predictions.jsonl",local)
    result={"schema":1,"source_cache_only":offline,"asset_counts":{"previous":previous,"current":current},
            "isolated_python":True,"python":sys.version.split()[0],
            "dependencies":{k:version(k) for k in ("onnxruntime","numpy","tokenizers","duckdb")},
            "reused_prior_predictions":False,"regenerated_previous_input_counts":[primary["retained_rows"],org["rows"]],
            "regenerated_inputs":new["retained"],"inputs_sha256":new["inputs_sha256"],"gold_sha256":new["gold_sha256"],
            "predictions_sha256":receipt["predictions_sha256"],"prediction_bytes_match_reference":exact,
            "full_aggregate_matches_reference":True,"original_trace_sql_and_envelope_check":exact,
            "optional_private_48_row_audit_used":False}
    save_json(out/"replay-receipt.json",result)
    print("Reproduced",new["retained"],"paired inputs. Aggregate match: yes. Prediction bytes match:",exact,flush=True)
    if timings:
        from .measure import run
        run(old,seal/"inputs.jsonl",out/"local-footprint.json")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True,help="new directory; never overwrite a previous run")
    p.add_argument("--asset-cache",type=Path,action="append",default=[],help="optional existing raw source directory, repeatable")
    p.add_argument("--offline",action="store_true",help="forbid downloading missing artifacts")
    p.add_argument("--timings",action="store_true",help="also run the independent 3×3 resource study")
    args=p.parse_args()
    try:replay(args.out,args.asset_cache,args.offline,args.timings)
    except (ValueError,OSError) as exc:p.exit(2,str(exc)+"\n")
