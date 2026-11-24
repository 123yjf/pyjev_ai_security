"""Prepare paired inputs and a separate scoring key. Never run either detector here."""
import argparse
from collections import Counter, defaultdict
import csv
import re
import unicodedata
from pathlib import Path
from .common import checked, digest, filehash, jsonl, save_json, save_rows, wire

# Zero-based PHYSICAL rows of the pinned Parquet files; pre-scoring, single reviewer.
# Priority is communicative purpose, not the mere presence of punctuation.
MENTION = {"docs": {288, 2317, 2443, 2533}, "direct": {350}}
QUOTE_DESIGN = {"docs": {1984, 2236, 2770, 2809, 2995}, "direct": set(range(1519, 1525))}
# Conservative sector selection at document-family level. Omit public administration,
# household finance tutorials, and both hospital/medical families from business primary.
NON_ENTERPRISE = {i for start in (287, 419, 2442, 3249) for i in range(start, start + 3)}
BUSINESS_DIGEST = "142f25b2db123103d11280481ce5c9a6b8c76fa95ef8dcb660e5090dd3925569"

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFKC", s).casefold() if c.isalnum())

def shingles(s):
    return {s[j:j+5] for j in range(max(0, len(s)-4))}

def parquet(path):
    import duckdb
    # Explicit physical order, not DuckDB's unspecified parallel scan order.
    db = duckdb.connect()
    try:
        q = db.execute("select * exclude(file_row_number) from read_parquet(?, file_row_number=true) order by file_row_number", [str(path)])
        names = [d[0] for d in q.description]
        return [dict(zip(names, x)) for x in q.fetchall()]
    finally:
        db.close()

def item(src, ix, text, label, strata):
    if not isinstance(text, str) or not text.strip() or label not in (0, 1):
        raise ValueError("unexpected benchmark schema")
    key = digest((src + ":" + str(ix)).encode())
    return dict(id=key, text=text, label=label, source=src, strata=sorted(strata))

def candidates(data):
    items, totals = [], {}
    for src in ("docs", "direct"):
        rows = parquet(checked(data, src+".parquet"))
        counts = Counter()
        for i, v in enumerate(rows):
            counts["all"] += 1
            if v["lang"] != "zh":
                continue
            counts["requested_zh"] += 1
            if v["lang_detected"] != "zh":
                continue
            counts["both_zh"] += 1
            y, s = v["label"], v["text"]
            strata = [src, src + "_" + v["source"].rsplit("/", 1)[1]]
            if src == "docs" and i not in NON_ENTERPRISE:
                strata.append("business_docs")
            if i in MENTION[src] or i in QUOTE_DESIGN[src]:
                if y != 0:
                    raise ValueError("negative communicative subgroup has non-benign label")
                strata += ["mention_or_quote", "risk_discussion" if i in MENTION[src] else "quoted_design"]
            # Purely typographic secondary positive stratum, not a speech-act gold label.
            if y and re.search("“[^”]+”|‘[^’]+’|「[^」]+」", s, re.S):
                strata.append("positive_quote_marks")
            items.append(item(src, i, s, y, strata))
        totals[src] = dict(counts)
    counts = Counter()
    for v in jsonl(checked(data,"agent-bench.jsonl")):
        c = v["category"]
        counts[c] += 1
        if c == "destructive":
            continue
        if c not in ("benign", "prompt_injection"):
            raise ValueError("unknown action category")
        items.append(item("agent", v["id"], v["context"], int(c == "prompt_injection"), ["agent"]))
    totals["agent"] = dict(counts)
    if len({v["id"] for v in items}) != len(items):
        raise ValueError("duplicate item key")
    return items, totals

def histories(data, prior, business_py=None):
    from research.curriculum import lessons
    from pyjev._office import exam
    for name in ("h-train", "h-val", "h-test"):
        yield name, (v["text"] for v in jsonl(checked(data,name+".jsonl")))
    for name in ("ds-train","ds-test","ri-train","ri-test"):
        yield name, (v["text"] for v in parquet(checked(data,name+".parquet")))
    for name in ("legacy","external"):
        yield name, (v["text"] for v in jsonl(checked(prior,name+".jsonl")))
    yield "pyjev-lessons", (r[0] for r in lessons())
    yield "pyjev-office", (r[0] for r in exam())
    with checked(data,"xstest.csv").open(encoding="utf-8-sig", newline="") as f:
        yield "xstest-safe", (v["prompt"] for v in csv.DictReader(f) if v["label"]=="safe")
    if business_py is not None:
        # Data-only extraction: no third-party Python is imported or executed.
        import ast
        if filehash(business_py) != BUSINESS_DIGEST:
            raise ValueError("old business fixture source changed")
        tree = ast.parse(Path(business_py).read_text())
        variables = {n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("SCENES","FRAMES")}
        yield "previous-business48", (fr.format(s) for s in variables["SCENES"] for fr in variables["FRAMES"])

def overlap(items, refs):
    # Index held-out rows only. No dense NxM distance matrix; intersection exact.
    by_norm, posting = defaultdict(set), defaultdict(set)
    sets = []
    for i, v in enumerate(items):
        k = norm(v["text"])
        if not k:
            raise ValueError("empty normalized record")
        by_norm[k].add(i)
        g = shingles(k); sets.append(g)
        for term in g:
            posting[term].add(i)
    matches = set()
    audit = {}
    for name, texts in refs:
        ex, near, n = set(), set(), 0
        for s in texts:
            n += 1
            k = norm(s); ex.update(by_norm.get(k, ()))
            g = shingles(k)
            if not g:
                continue
            hits = Counter(i for term in g for i in posting.get(term, ()))
            for i, h in hits.items():
                if 10*h >= 7*(len(g)+len(sets[i])-h):
                    near.add(i)
        audit[name] = {"rows":n,"exact":len(ex),"near_only":len(near-ex)}
        matches.update(ex | near)
    # Drop ALL copies of an internal exact-normalized duplicate, including disagreements.
    duplicates = {i for group in by_norm.values() if len(group)>1 for i in group}
    retained = set(range(len(items))) - matches - duplicates
    near_pairs = 0
    for i in retained:
        others = Counter(j for t in sets[i] for j in posting[t] if j>i and j in retained)
        near_pairs += sum(10*h >= 7*(len(sets[i])+len(sets[j])-h) for j,h in others.items())
    return retained, dict(reference=audit, excluded_prior=len(matches), internal_exact_rows=len(duplicates),
                          retained_internal_near_pairs=near_pairs)

def prepare(data, prior, business, out):
    xs, inventory = candidates(data)
    keep, audit = overlap(xs, histories(data, prior, business))
    rows = sorted((xs[i] for i in keep),key=lambda r:r["id"])
    out.mkdir(parents=True,exist_ok=True)
    inputs = out/"inputs.jsonl"; gold = out/"gold.jsonl"
    save_rows(inputs, ({"id":r["id"],"text":r["text"]} for r in rows))
    save_rows(gold, ({k:v for k,v in r.items() if k!="text"} for r in rows))
    counts = Counter(k for r in rows for k in r["strata"])
    receipt = {"schema":1, "candidate_rows":len(xs), "retained_rows":len(rows),
               "inventory":inventory,"overlap":audit,"strata":dict(counts),
               "inputs_sha256":filehash(inputs),"gold_sha256":filehash(gold)}
    save_json(out/"cohort.json",receipt)
    return receipt

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--prior-dir",type=Path,help="directory containing the two historical public JSONL files (default: --data)")
    p.add_argument("--business-fixture",type=Path,help="optional original 48-row synthetic historical control source; checksum required")
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=prepare(a.data,a.prior_dir or a.data,a.business_fixture,a.out)
    print(wire({k:result[k] for k in ("candidate_rows","retained_rows","inputs_sha256","gold_sha256")}))
