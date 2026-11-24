"""Prepare the blind cohort only. No calls to, or output from, any classifier."""
import argparse,ast,json,re
from collections import Counter
from pathlib import Path
from research.enterprise.common import digest,filehash,jsonl,save_json,save_rows
from research.enterprise.prepare import histories,overlap
from .development import records
HERE=Path(__file__).parent
INDEX=json.loads((HERE/"sources.json").read_text())
# Verbatim, inclusive and disjoint ranges reviewed BEFORE inference. No extra framing.
GUIDE={
 "basics": {"d":[(8,8),(30,30),(48,50),(73,73),(92,92)],"q":[(32,40),(66,71),(84,90)]},
 "elements":{"d":[(3,13),(27,27)],"q":[(15,23),(25,25)]},
 "tips":{"d":[(7,11),(15,17),(40,42),(68,68),(85,85)],"q":[(19,30),(44,55),(70,74),(76,80),(87,96),(104,112)]},
 "examples":{"d":[(40,40),(58,58),(82,84),(118,118),(137,137)],"q":[(24,32),(66,74),(92,104),(120,129)]},
 "fewshot":{"d":[(3,5),(21,27),(44,44),(60,60),(105,107)],"q":[(7,14),(29,37),(64,70),(80,98)]},
 "function":{"d":[(5,9),(13,18)],"q":[(22,30)]},
 "workplace":{"d":[(3,5),(7,15)],"q":[]},
 "zeroshot":{"d":[(17,21)],"q":[(2,10)]}}
def check_files(data):
    for k,v in INDEX.items():
        if filehash(data/k)!=v["sha256"]:raise ValueError("source changed: "+k)
def item(src,key,text,y,kind,group=None,speech=None):
    if not isinstance(text,str) or not text.strip() or y not in (0,1):raise ValueError("invalid input")
    return dict(id=digest((src+":"+str(key)).encode()),text=text,label=y,kind=kind,group=group,speech=speech)
def blind(data):
    xs=[];inj=list(jsonl(data/"injectagent-cn.jsonl"));ace=list(jsonl(data/"acebench-zh-agent.jsonl"))
    assert len(inj)==450 and len(ace)==401
    for v in inj:
        group=re.fullmatch(r"injectagent-cn:(UC-[0-9]+)-AT-[0-9]+",v["id"])[1]
        assert v["label"]==1
        xs.append(item("inj",v["id"],v["text"],1,"tool_injected",group))
    tree=ast.parse((data/"reference-structure.py").read_text())
    records0=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and getattr(n.targets[0],"id","")=="USER_CASES")
    assert len(records0)==15
    for v in records0:
        s=v["response_template"]; marker="<ATTACKER_INSTRUCTION>"
        assert s.count(marker)==1
        xs.append(item("blank",v["id"],s.replace(marker,""),0,"tool_clean",v["id"]))
    assert {x["group"] for x in xs if x["label"]}=={x["group"] for x in xs if not x["label"]}
    ordered=sorted(ace,key=lambda r:digest(r["id"].encode()))
    for i,v in enumerate(ordered):
        assert v["label"]==0
        # Desire statements lacking a direct assignment, or a question asking HOW to do
        # something, do not establish that the assistant should perform that action.
        s=None if i>=24 else ("ambiguous" if i in (5,11,16) else "act")
        xs.append(item("task",v["id"],v["text"],0,"agent_task",v["source_split"],s))
    for name,groups in GUIDE.items():
        lines=(data/f"guide-{name}.mdx").read_text().splitlines(); covered=set()
        for k,ranges in groups.items():
            for i,j in ranges:
                a=set(range(i,j+1)); assert 1<=i<=j<=len(lines) and not covered&a;covered|=a
                txt="\n".join(lines[i-1:j]); assert re.search(r"[\u3400-\u9fff]",txt)
                xs.append(item("guide",f"{name}:{i}-{j}",txt,0,"guide_quote" if k=="q" else "guide_discussion",name,"mention"))
    for name,v in INDEX.items():
        if name.endswith(".article"):
            xs.append(item("case",v["url"],(data/name).read_text(),v["category"],"incident_description"))
    assert len({v["id"] for v in xs})==len(xs)
    return xs
def prepare(data,old,prior,business,out):
    check_files(data);xs=blind(data)
    # Independent hash checks of the PREVIOUS study seals prior to using them as exclusions.
    seals=[]
    for sub,key in [("seal","cohort"),("orgseal","org-cohort")]:
        rec=json.loads((HERE.parent/"enterprise"/(key+".json")).read_text())
        inp=old/sub/"inputs.jsonl"
        if filehash(inp)!=rec["inputs_sha256"]:raise ValueError("historical seal mismatch")
        seals.append((sub,[v["text"] for v in jsonl(inp)]))
    refs=list((n,list(s)) for n,s in histories(old,prior,business))+seals+[("current_development",[t for _,_,t in records(data)])]
    keep,audit=overlap(xs,refs)
    rows=sorted((xs[i] for i in keep),key=lambda v:v["id"])
    out.mkdir(exist_ok=False)
    save_rows(out/"inputs.jsonl",({"id":v["id"],"text":v["text"]} for v in rows))
    save_rows(out/"gold.jsonl",({k:w for k,w in v.items() if k!="text"} for v in rows))
    receipt=dict(inputs_sha256=filehash(out/"inputs.jsonl"),gold_sha256=filehash(out/"gold.jsonl"),
                 candidate_commit="fb2bdf233010ad1887d9d9aa31aa1873e97fc1d5",retained=len(rows),before=len(xs),
                 kinds=dict(Counter(v["kind"] for v in rows)),overlap=audit)
    save_json(out/"cohort.json",receipt);print("cohort:",len(xs),len(rows),receipt["kinds"])
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("data","old","prior","business","out"):p.add_argument("--"+n,required=True,type=Path)
    prepare(**vars(p.parse_args()))
