"""Run one prespecified original-PyBot experiment in a local, read-only, networkless container.
Does not clone source, download data, install a dependency or overwrite an existing result.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from research.compare_pybot import REV, TREE, WRAPPER, digest
from research.replay import SOURCES

IMAGE="python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535"

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--upstream",required=True,type=Path,help="existing Git checkout of original pybot")
    p.add_argument("--external",required=True,type=Path);p.add_argument("--legacy",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path,help="new filename for aggregate results only")
    p.add_argument("--mode",choices=("task","raw"),default="task");p.add_argument("--jobs",type=int,choices=range(1,9),default=None)
    a=p.parse_args(argv);jobs=a.jobs or (4 if a.mode=="task" else 2);root=Path(__file__).resolve().parents[1];up=a.upstream.resolve()
    if a.out.exists() or not a.out.parent.is_dir():p.error("choose a new output filename in an existing directory")
    if subprocess.check_output(["git","-C",str(up),"rev-parse","HEAD"],text=True).strip()!=REV:p.error("wrong upstream commit")
    for suite,file in (("external",a.external),("legacy",a.legacy)):
        h,n=SOURCES[suite]
        with file.open("rb") as f:b=f.read(n+1)
        if digest(b)!=h:p.error("dataset checksum mismatch")
    endpoint=os.environ.get("DOCKER_HOST") or subprocess.check_output(["docker","context","inspect","--format","{{.Endpoints.docker.Host}}"],text=True).strip()
    if not (endpoint.startswith("unix://") or endpoint.startswith("npipe://")):p.error("a local Docker daemon is required")
    command=["docker","run","--rm","--pull","never","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges",
             "--user","65534:65534","--pids-limit","80","--memory","3500m","--memory-swap","3500m","--cpus",str(jobs),"--workdir","/app",
             "-e","PYTHONHASHSEED=0","-e","PYTHONDONTWRITEBYTECODE=1","-e","OPENBLAS_NUM_THREADS=1"]
    for local,mount in ((root/"pyjev","/app/pyjev"),(root/"research","/app/research"),
                        (root/"research/fixtures/pybot-protocol-registered.utf8","/app/research/PYBOT_PROTOCOL.md"),
                        (up/"pybot.py","/upstream/pybot.py"),
                        (up/"bot","/upstream/bot"),(a.external.resolve(),"/data/external.jsonl"),(a.legacy.resolve(),"/data/legacy.jsonl")):
        if "," in str(local):p.error("mount paths must not contain commas")
        command+=["--mount",f"type=bind,src={local},dst={mount},readonly"]
    entry="research.compare_pybot" if a.mode=="task" else "research.raw_control"
    command += [IMAGE,"python","-B","-m",entry,"--pybot","/upstream","--external","/data/external.jsonl","--legacy","/data/legacy.jsonl","--jobs",str(jobs)]
    cp=subprocess.run(command,stdout=subprocess.PIPE)
    if cp.returncode:return cp.returncode
    try:r=json.loads(cp.stdout)
    except ValueError:p.error("no complete aggregate; refusing to write")
    if r.get("pybot_commit")!=REV or r.get("raw_texts_exported")!=0 or r.get("total_cases",r.get("n"))!=(2057 if a.mode=="task" else 673):
        p.error("run not complete; refusing to write")
    with a.out.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2,sort_keys=True); f.write("\n")
    return 0
if __name__=="__main__":raise SystemExit(main())
