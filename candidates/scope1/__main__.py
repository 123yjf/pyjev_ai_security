"""Read one text privately from stdin. Emit decisions, never the input."""
import argparse
import json
import sys
from . import ScopeAuditor
from .view import MAX

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json",action="store_true",help="machine-readable routing decision")
    args=p.parse_args()
    try:s=sys.stdin.buffer.read(4*MAX+1).decode("utf8","strict")
    except UnicodeError:s=None
    r=ScopeAuditor().audit(s)
    if args.json:print(json.dumps(r.as_dict(),ensure_ascii=False,sort_keys=True))
    else:print(f"{r.route} · {r.speech_act} · execution: {r.execution_evidence}")
    return 2 if r.needs_review is None else 0
if __name__=="__main__":raise SystemExit(main())
