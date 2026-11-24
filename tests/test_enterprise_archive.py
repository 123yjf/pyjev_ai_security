"""Archive consistency: no models, private data or network required."""
import json
from pathlib import Path
import unittest
from research.enterprise.common import HERE
from research.enterprise.score import MODES

class EnterpriseArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((HERE/"cohort.json").read_text())
        cls.r=json.loads((HERE/"results.json").read_text())
        cls.g=cls.r["groups"]

    def test_checksums_and_coverage(self):
        self.assertEqual(self.r["receipt"],json.loads((HERE/"prediction-receipt.json").read_text()))
        self.assertEqual(self.c["inputs_sha256"],self.r["receipt"]["inputs_sha256"])
        self.assertEqual(self.c["retained_rows"],self.r["receipt"]["rows"])
        self.assertEqual(sum(v["rows"] for v in self.c["overlap"]["reference"].values()),53029)
        for k,row in self.g.items():
            self.assertEqual(row["positive"]+row["negative"],row["n"])
            if k!="all":self.assertEqual(row["n"],self.c["strata"][k])
            for v in row["modes"].values():
                self.assertEqual(v["tp"]+v["fn"]+v["missing_pos"],row["positive"])
                self.assertEqual(v["tn"]+v["fp"]+v["missing_neg"],row["negative"])
            for kind,key in (("negative","fp"),("positive","fn")):
                pair=row["paired"][kind]
                self.assertEqual(sum(pair.values()),row[kind])
                self.assertEqual(pair["incomplete"],0)
                self.assertEqual(pair["both_wrong"]+pair["only_pyjev_wrong"],row["modes"]["pyjev"][key])
                self.assertEqual(pair["both_wrong"]+pair["only_hikma_wrong"],row["modes"]["hikma_050"][key])
        for kind,subgroups in (("all",("docs","direct","agent")),("mention_or_quote",("risk_discussion","quoted_design"))):
            for mode in MODES:
                for stat in ("fp","fn","tp","tn","missing_pos","missing_neg"):
                    self.assertEqual(self.g[kind]["modes"][mode][stat],sum(self.g[k]["modes"][mode][stat] for k in subgroups))

    def test_printed_primary_tables_match_machine_counts(self):
        report=(HERE.parents[1]/"docs"/"enterprise-blind.md").read_text()
        for k in ("business_docs","docs","direct","agent"):
            group=self.g[k]
            cells=[f'{group["positive"]} / {group["negative"]}']
            for key,den in (("fn","positive"),("fp","negative")):
                d=group[den]
                for mode in ("pyjev","hikma_050"):
                    e=group["modes"][mode][key]
                    cells.append(f"{e}/{d} ({100*e/d:.1f}%)")
            self.assertIn(" | ".join(cells),report)
        for key in ("risk_discussion","quoted_design","mention_or_quote"):
            group=self.g[key];d=group["negative"]
            cells=[str(d)]
            for mode in ("pyjev","hikma_050"):
                e=group["modes"][mode]["fp"]
                cells.append(f"{e}/{d} ({100*e/d:.1f}%)")
            self.assertIn(" | ".join(cells),report)

    def test_separate_real_negative_controls(self):
        result=json.loads((HERE/"org-results.json").read_text())
        seal=json.loads((HERE/"org-cohort.json").read_text())
        self.assertEqual(result["receipt"],json.loads((HERE/"org-prediction-receipt.json").read_text()))
        self.assertEqual(result["receipt"]["inputs_sha256"],seal["inputs_sha256"])
        self.assertEqual(seal["rows"],47)
        self.assertEqual(seal["overlap"]["reference"]["earlier455"]["rows"],455)
        self.assertEqual(seal["overlap"]["excluded_prior"],0)
        g=result["groups"]
        for k,row in g.items():
            self.assertEqual(row["positive"],0)
            for mode,d in row["modes"].items():
                self.assertEqual(row["n"],d["fp"]+d["tn"])
                self.assertFalse(d["missing_neg"])
                if k=="all":
                    self.assertEqual(d["fp"],sum(g[s]["modes"][mode]["fp"] for s in ("antd","tdesign")))
        self.assertEqual(g["all"]["modes"]["pyjev"]["fp"],1)
        self.assertEqual(g["all"]["modes"]["hikma_050"]["fp"],47)
        report=(HERE.parents[1]/"docs"/"enterprise-blind.md").read_text()
        for k in ("antd","tdesign"):
            n=g[k]["n"]; a=g[k]["modes"]["pyjev"]["fp"];b=g[k]["modes"]["hikma_050"]["fp"]
            self.assertIn(f"| {n} | {a}/{n} | {b}/{n} |",report)
