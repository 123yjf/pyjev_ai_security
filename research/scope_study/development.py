"""Development materials only. Never import the blind preparation or scoring modules."""
from collections import Counter, defaultdict
from pathlib import Path
import re
from research.enterprise.prepare import parquet
from candidates.scope1 import ScopeAuditor

def prose(path):
    paragraph=[]; fence=None
    for line in path.read_text().splitlines()+[""]:
        st=line.strip()
        border=re.match(r"^(\x60{3,}|~{3,})",st)
        if border:
            if fence is None: fence=border[1][0]
            elif border[1][0]==fence:fence=None
            st=""
        elif fence is not None:continue
        if not st or st.startswith(("#","<","import ","export ","---","![")):
            if paragraph:
                s="\n".join(paragraph)
                if 16<=len(s)<=900 and len(re.findall("[\u3400-\u9fff]",s))>=8 and "http" not in s:
                    yield s
            paragraph=[]
        else:paragraph.append(line)
def records(root):
    for r in parquet(root/"horizon-v2.parquet"):
        if r["lang"]==r["lang_detected"]=="zh":yield "horizon",r["label"],r["text"]
    for p in sorted(root.glob("dify-*.mdx")):
        for s in prose(p):yield "dify",0,s
    raw=(root/"owasp01.md").read_text()
    for block in re.split(r"(?m)^#### 场景 [^\n]+\n",raw)[1:]:
        yield "owasp_cases",1,block.strip().split("\n\n",1)[0].strip()
def measure(root):
    m=ScopeAuditor();out=defaultdict(Counter)
    for src,y,t in records(root):
        d=m.audit(t); a=d.original_review=="review";b=d.needs_review
        assert b is not None
        c=out[src];c["rows"]+=1;c["positives"]+=y
        for k,p in [("base",a),("candidate",b)]:
            c[k+("_fn" if y else "_fp")]+=int(bool(p)!=bool(y))
        c["lost_tp"]+=int(y and a and not b)
    return {k:dict(c) for k,c in out.items()}
if __name__=="__main__":
    import sys,json
    print(json.dumps(measure(Path(sys.argv[1])),sort_keys=True))
