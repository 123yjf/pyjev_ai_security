"""Download only checksum-pinned public artifacts. Never sends samples for inference."""
import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, urlopen
from .common import CATALOG, filehash

def fetch(root,name,spec):
    dest=root/name
    if dest.exists():
        if filehash(dest)!=spec["sha256"]: raise ValueError("existing file mismatch: "+name)
        return
    url=spec["url"]
    if not url.startswith("https://"):raise ValueError("HTTPS only")
    for suffix in ("","?download=true"):
        try:
            with tempfile.TemporaryFile(dir=root) as tmp:
                h=hashlib.sha256();size=0
                with urlopen(Request(url+suffix,headers={"User-Agent":"PyJev-pinned-artifact/1"}),timeout=90) as res:
                    if not res.geturl().startswith("https://"):raise ValueError("insecure redirect")
                    while chunk:=res.read(1<<20):
                        size+=len(chunk)
                        if size>350_000_000:raise ValueError("unexpected size")
                        h.update(chunk);tmp.write(chunk)
                if h.hexdigest()!=spec["sha256"]:raise ValueError("pinned digest mismatch")
                tmp.seek(0)
                with dest.open("xb") as out:shutil.copyfileobj(tmp,out)
            return
        except OSError:
            if suffix:raise

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",required=True,type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    for name,spec in CATALOG.items():
        fetch(a.out,name,spec);print(name,"verified",flush=True)
