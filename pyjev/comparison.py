"""Read and validate measured baseline results. This is not a live run of either engine."""
from .api import _read, ModelIntegrityError

REV="7d63c7fbebb44c7e466e5c8b5c1f341ab767929e"
SUITES=("office","external","legacy")
SETTINGS=("pyjev","pybot_task","pybot_raw")

def measured():
    a=_read("pybot-comparison.json");b=_read("pybot-raw-control.json")
    if not (a["pybot_commit"]==b["pybot_commit"]==REV and a["official_cli_parity"] and a["total_cases"]==2057 and b["n"]==673):
        raise ModelIntegrityError("Invalid comparison cohort or reference")
    vals={"pyjev":a["systems"]["pyjev"],"pybot_task":a["systems"]["original_pybot"],"pybot_raw":b["system"]}
    for method,cohorts in vals.items():
        if set(cohorts)!=(set(SUITES[:2]) if method=="pybot_raw" else set(SUITES)):raise ModelIntegrityError("Missing cohort")
        for suite,row in cohorts.items():
            n={"office":320,"external":353,"legacy":1384}[suite];cm=row["confusion"]
            if (row["n"]!=n or row["valid"]+row["no_label"]+row["timeout"]+row["error"]!=n or
                row["completed"]!=n-row["timeout"]-row["error"] or row["correct"]!=sum(cols[gold] for gold,cols in cm.items()) or
                sum(sum(v.values()) for v in cm.values())!=n or not 0<=row["correct"]<=row["valid"]<=n):
                raise ModelIntegrityError("Inconsistent comparison counts")
    return vals

def compact():
    measures=measured()
    rows=[]
    for suite in SUITES:
        for system in SETTINGS:
            r=measures[system].get(suite)
            if r is None: continue  # not run, never encoded as a zero-count experiment
            row={f:r[f] for f in ("n","valid","correct","no_label","timeout","error","accuracy_conditional_on_valid")}
            row.update(system=system,suite=suite,label_coverage=r["valid"]/r["n"],correct_over_all=r["correct"]/r["n"])
            if suite != "office":
                row.update({k:r[k] for k in ("false_positives","valid_normals","fpr_scored",
                                             "true_positives","valid_positives","recall_scored")})
            rows.append(row)
    return {"source":"frozen_original_pybot_comparison","pybot_commit":REV,
        "rows":rows}
