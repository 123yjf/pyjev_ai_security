"""Independent SQL tally of all blind primary cells, plus carrier and receipt checks."""
import argparse,ast,json,re
from collections import Counter
from pathlib import Path
from research.enterprise.common import filehash,jsonl
from .prepare import HERE,INDEX

def verify(data,seal,pred,stats):
    import duckdb
    s=json.loads((HERE/"cohort.json").read_text());r=json.loads((HERE/"prediction-receipt.json").read_text())
    assert filehash(seal/"gold.jsonl")==s["gold_sha256"] and filehash(seal/"inputs.jsonl")==s["inputs_sha256"]
    assert filehash(pred)==r["predictions_sha256"] and r["inputs_sha256"]==s["inputs_sha256"]
    db=duckdb.connect()
    try:
        for table,path in (("g",seal/"gold.jsonl"),("p",pred)):
            db.read_json(str(path),format="newline_delimited").create_view(table)
        assert db.sql("select count(*),count(distinct id) from g join p using(id)").fetchone()==(s["retained"],s["retained"])
        stats=json.loads(stats.read_text());cells=0
        for m,cond in [("v010","base='review'"),("scope","review"),("scope_active","scope='review'"),
                       ("hikma","p.p >= 0.5"),("hikma_sensitive","p.p>=0.005")]:
            # There were no incomplete cases in this delivery; if that changes, fail explicitly.
            assert db.sql("select count(*) from p where review is null or base='incomplete'").fetchone()[0]==0
            rows=db.sql("select kind,label,("+cond+") flagged,count(*) from g join p using(id) group by all").fetchall()
            counts=Counter({(k,int(y),bool(f)):n for k,y,f,n in rows})
            for k in {x[0] for x in rows}:
                z=stats["groups"][k]["modes"][m]
                assert [z[c] for c in ("tp","fn","fp","tn")]==[counts[k,y,f] for y,f in [(1,True),(1,False),(0,True),(0,False)]]
                cells+=4
    finally:db.close()
    # Verify actual publisher prefix/suffix alignment, not just provenance strings.
    struct=data/"reference-structure.py"
    assert filehash(struct)==INDEX[struct.name]["sha256"]
    cases=next(ast.literal_eval(n.value) for n in ast.parse(struct.read_text()).body if isinstance(n,ast.Assign) and getattr(n.targets[0],"id","")=="USER_CASES")
    carriers={x["id"]:x["response_template"].split("<ATTACKER_INSTRUCTION>") for x in cases};seen=Counter()
    for row in jsonl(data/"injectagent-cn.jsonl"):
        key=re.fullmatch(r"injectagent-cn:(UC-\d+)-AT-\d+",row["id"])[1];a,b=carriers[key]
        assert row["text"].startswith(a) and row["text"].endswith(b);seen[key]+=1
    assert len(seen)==15 and set(seen.values())=={30}
    print(f"Verified {cells} independently tallied cells and {sum(seen.values())} exact template envelopes.")
if __name__=="__main__":
    a=argparse.ArgumentParser()
    for k in ("data","seal","pred","stats"):a.add_argument("--"+k,type=Path,required=True)
    verify(**vars(a.parse_args()))
