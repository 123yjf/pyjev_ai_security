"""CPU-only resource replay of the sealed 924 inputs. The harness cannot read gold labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEALED = ROOT / "research" / "scope_study" / "cohort.json"
ENGINES = ("v010", "scope", "hikma")
ROUNDS = 3
WARMUP = tuple(f"会议第{i}项：请为本月的培训材料编制目录。" * repeat
               for i in range(1, 5) for repeat in (1, 3, 7))

def percentile(data, fraction):
    """Nearest-rank percentile. Do not assume a parametric distribution."""
    if not data or not 0 < fraction <= 1:
        raise ValueError("bad percentile argument")
    ordered = sorted(data)
    return ordered[math.ceil(len(ordered) * fraction) - 1]

def sealed_inputs(path):
    receipt = json.loads(SEALED.read_text(encoding="utf8"))
    b = path.read_bytes()
    if hashlib.sha256(b).hexdigest() != receipt["inputs_sha256"]:
        raise ValueError("not the preregistered input file; no performance comparison made")
    rows = [json.loads(line) for line in b.splitlines()]
    if (len(rows) != receipt["retained"] or len({r["id"] for r in rows}) != len(rows)
            or any(set(r) != {"id", "text"} for r in rows)):
        raise ValueError("unpaired schema")
    return rows

def load_engine(engine, models):
    if engine == "hikma":
        from research.enterprise.infer import Comparator
        detector = Comparator(models)
        return lambda text: detector.predict(text)[0] >= .5
    if engine == "v010":
        from pyjev import Auditor
        a = Auditor()
        def decide(text):
            r = a.audit(text).review
            return None if r == "incomplete" else r == "review"
        return decide
    if engine == "scope":
        from candidates.scope1 import ScopeAuditor
        a = ScopeAuditor()
        return lambda text: a.audit(text).needs_review
    raise ValueError("unknown engine")

def rss_mib():
    import resource
    if sys.platform not in ("darwin", "linux"):
        raise ValueError("peak RSS conversion is supported on Linux and macOS only")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / (2**20 if sys.platform == "darwin" else 1024)

def worker(engine, models, inputs, wave):
    rows = sealed_inputs(inputs)
    random.Random(71124 + wave).shuffle(rows)  # same order for all engines in a wave
    start = time.perf_counter_ns()
    decide = load_engine(engine, models)
    load_ms = (time.perf_counter_ns() - start) / 1e6
    for s in WARMUP:
        decide(s)
    latencies, flags = [], []
    cpu = time.process_time_ns()
    wall = time.perf_counter_ns()
    for row in rows:
        t = time.perf_counter_ns()
        flag = decide(row["text"])
        latencies.append(time.perf_counter_ns() - t)
        if flag is None:
            raise ValueError("unexpected unclassified item")
        flags.append(flag)
    elapsed = (time.perf_counter_ns() - wall) / 1e9
    cpu_ms = (time.process_time_ns() - cpu) / 1e6
    peak = rss_mib()
    bits = bytes(int(b) for _, b in sorted(zip((r["id"] for r in rows), flags)))
    # Individual times remain only in the parent process until quantiles are computed.
    return dict(times_ns=latencies,elapsed_s=elapsed,cpu_ms=cpu_ms,
                peak_rss_mib=peak,load_ms=load_ms,alerts=sum(flags),sha_flags=hashlib.sha256(bits).hexdigest())

def receipt_expected_counts():
    groups = json.loads((SEALED.parent / "blind-results.json").read_text())["groups"]
    return {k:sum(g["modes"][k]["tp"] + g["modes"][k]["fp"]
                  for g in (groups["operative_material"], groups["incident_description"]))
            for k in ENGINES}

def processor():
    if sys.platform == "darwin":
        return subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"],text=True).strip()
    if sys.platform == "linux":
        with Path("/proc/cpuinfo").open() as f:
            for line in f:
                if line.startswith("model name") and ":" in line:
                    return line.split(":",1)[1].strip()
    return platform.machine()

def size_assets(models, engine):
    if engine == "hikma":
        files = (models/"detector.onnx",models/"tokenizer.json")
    else:
        files = tuple(ROOT/"pyjev"/"data"/n for n in ("head.json","rulebook.json"))
    return sum(p.stat().st_size for p in files)

def group_metric(runs, size):
    all_ns = [v for r in runs for v in r["times_ns"]]
    n=len(all_ns); wall=sum(r["elapsed_s"] for r in runs)
    def rounded(x):return round(x,5)
    return dict(timed=n,alerts_per_round=runs[0]["alerts"],decision_digest=runs[0]["sha_flags"],
                p50_ms=rounded(percentile(all_ns,.5)/1e6),p95_ms=rounded(percentile(all_ns,.95)/1e6),
                p99_ms=rounded(percentile(all_ns,.99)/1e6),process_cpu_ms_per_text=rounded(sum(r["cpu_ms"] for r in runs)/n),
                sequential_texts_per_s=rounded(n/wall),maximum_process_peak_rss_mib=rounded(max(r["peak_rss_mib"] for r in runs)),
                median_engine_load_ms=rounded(statistics.median(r["load_ms"] for r in runs)),
                inference_asset_bytes=size,rounds=[dict(n=len(r["times_ns"]),p50_ms=rounded(percentile(r["times_ns"],.5)/1e6),
                    p95_ms=rounded(percentile(r["times_ns"],.95)/1e6),wall_s=rounded(r["elapsed_s"]),
                    process_cpu_ms=rounded(r["cpu_ms"]),peak_rss_mib=rounded(r["peak_rss_mib"]),load_ms=rounded(r["load_ms"]))
                    for r in runs])
def run(models, inputs, output):
    from importlib.metadata import version
    if output.exists():raise FileExistsError("choose a new aggregate output path")
    rows=sealed_inputs(inputs);expected=receipt_expected_counts()
    env=os.environ.copy()
    env.update(PYTHONHASHSEED="0",PYTHONNOUSERSITE="1",OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1",TOKENIZERS_PARALLELISM="false",HF_HUB_OFFLINE="1")
    runs={k:[] for k in ENGINES}; orders=[]
    for i in range(ROUNDS):
        order=ENGINES[i:]+ENGINES[:i];orders.append(order)
        for k in order:
            args=[sys.executable,"-s","-m","research.footprint.measure","--models",str(models.resolve()),
                  "--inputs",str(inputs.resolve()),"--worker",k,"--wave",str(i)]
            child=subprocess.run(args,env=env,cwd=ROOT,check=True,stdout=subprocess.PIPE,text=True,timeout=600)
            r=json.loads(child.stdout)
            if len(r["times_ns"])!=len(rows) or r["alerts"]!=expected[k]:
                raise ValueError("unexpected coverage or frozen decision count: "+k)
            if runs[k] and runs[k][0]["sha_flags"]!=r["sha_flags"]:raise ValueError("nondeterministic labels")
            runs[k].append(r)
            print(f"process {i+1}/{ROUNDS} · {k}: {len(rows)} texts",flush=True)
    lens=[len(r["text"]) for r in rows]
    report={"schema":1,"scope":"frozen corpus runtime replay, not a new accuracy test or service capacity",
            "candidate_commit":"fb2bdf233010ad1887d9d9aa31aa1873e97fc1d5","baseline_tag":"v0.1.0",
            "comparator_revision":"b7d8317a617012d23713f4999acaba0690bc1c73","inputs_sha256":json.loads(SEALED.read_text())["inputs_sha256"],
            "environment":{"cpu":processor(),"os":platform.system(),"os_version":platform.mac_ver()[0] or platform.release(),
                           "arch":platform.machine(),"logical_cpus":os.cpu_count(),"python":platform.python_version(),
                           "numpy":version("numpy"),"onnxruntime":version("onnxruntime"),"tokenizers":version("tokenizers"),
                           "provider":"CPUExecutionProvider","ort_intra_threads":2,"ort_inter_threads":1},
            "unique_inputs":len(rows),"input_characters":{"min":min(lens),"p50":percentile(lens,.5),"p95":percentile(lens,.95),"max":max(lens)},
            "fresh_processes":ROUNDS*len(ENGINES),"warmups_per_process":len(WARMUP),"batch":1,"order":orders,
            "engines":{k:group_metric(rs,size_assets(models,k)) for k,rs in runs.items()}}
    with output.open("x",encoding="utf8") as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models",type=Path,required=True);p.add_argument("--inputs",type=Path,required=True)
    p.add_argument("--out",type=Path);p.add_argument("--worker",choices=ENGINES,help=argparse.SUPPRESS)
    p.add_argument("--wave",type=int,default=0,help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.worker:print(json.dumps(worker(a.worker,a.models,a.inputs,a.wave),allow_nan=False))
    elif a.out:run(a.models,a.inputs,a.out)
    else:p.error("--out required")
