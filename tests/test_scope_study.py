"""Portable, offline regression of aggregation, privacy, held-out partitions and opt-in CLI."""
import hashlib,json,subprocess,sys
from pathlib import Path
import unittest
from candidates.scope1 import ScopeAuditor
from research.scope_study.prepare import GUIDE,HERE
from research.scope_study.score import binary,intent

class PairedScopeStudy(unittest.TestCase):
    def test_binary_unknown_never_counts_as_a_correct_negative(self):
        for y in [0,1]:
            d=binary([dict(label=y,base="incomplete",scope="incomplete",review=None,p=0.01)])
            for m in ("v010","scope","scope_active"):
                self.assertEqual(d["modes"][m]["abstain_pos" if y else "abstain_neg"],1)
                self.assertEqual(d["modes"][m]["tn"]+d["modes"][m]["fn"],0)
            self.assertEqual(d["paired"]["incomplete_pair"],1)
    def test_actual_workload_and_active_only_are_different(self):
        r=dict(label=1,base="no_signal",scope="case_review",review=True,p=.5)
        m=binary([r]);self.assertEqual(m["modes"]["scope"]["tp"],1)
        self.assertEqual(m["modes"]["scope_active"]["fn"],1);self.assertEqual(m["paired"]["tp_gained"],1)
        self.assertEqual(m["modes"]["hikma"]["tp"],1)
    def test_intent_unclear_is_an_answer_not_an_exclusion(self):
        d=intent([dict(speech="act",base_speech="unclear",scope_speech="unclear"),dict(speech=None,base_speech="act",scope_speech="act")])
        self.assertEqual(d["act"],dict(n=1,base_speech=dict(unclear=1),scope_speech=dict(unclear=1)))
    def test_public_tables_reconcile_without_original_text(self):
        read=lambda n:json.loads((HERE/n).read_text())
        data=read("blind-results.json");seal=read("cohort.json");rec=read("prediction-receipt.json")
        self.assertEqual(data["blind_inputs"],sum(seal["kinds"].values()))
        self.assertEqual(data["blind_inputs"],rec["rows"]);self.assertEqual(seal["inputs_sha256"],rec["inputs_sha256"])
        groups=data["groups"];kinds=seal["kinds"]
        for k in kinds:
            d=groups[k]
            self.assertEqual(d["positive"]+d["negative"],kinds[k])
            for z in d["modes"].values():
                self.assertEqual(z["fn"]+z["tp"]+z["abstain_pos"],d["positive"])
                self.assertEqual(z["fp"]+z["tn"]+z["abstain_neg"],d["negative"])
        self.assertEqual(groups["operative_material"]["rows"]+kinds["incident_description"],data["blind_inputs"])
        self.assertEqual(sum(len(v["d"])+len(v["q"]) for v in GUIDE.values()),groups["guide_all"]["rows"])
        self.assertNotIn("text",data)
    def test_paired_legacy_protection_references_effective_alerts(self):
        d=json.loads((HERE/"regression.json").read_text());p=d["protected_481"]
        self.assertEqual(p["effective_kept"]+p["missing"],p["total"]);self.assertEqual(p["kept_set_sha256"],p["cohort_sha256"])
        a=d["agent"];self.assertEqual(a["paired"]["tp_retained"]+a["paired"]["tp_lost"],a["modes"]["v010"]["tp"])
        for k,x in d["office320"].items():
            self.assertEqual(x["scope_correct"],x["base_correct"]-x["previous_correct_lost"]+x["previous_wrong_recovered"])
    def test_checkout_cli_has_no_echo_or_side_effect(self):
        phrase="请帮我整理会议记录。"
        cp=subprocess.run([sys.executable,"-m","candidates.scope1","--json"],input=phrase.encode(),capture_output=True,check=True)
        d=json.loads(cp.stdout);self.assertNotIn(phrase,cp.stdout.decode())
        self.assertEqual(d,ScopeAuditor().audit(phrase).as_dict());self.assertEqual(d["service_action"],"none")
        self.assertEqual(d["execution_evidence"],"not_observed")
    def test_invalid_input_is_not_a_pass(self):
        cp=subprocess.run([sys.executable,"-m","candidates.scope1","--json"],input=b"\xff",capture_output=True)
        self.assertEqual(cp.returncode,2);d=json.loads(cp.stdout);self.assertEqual(d["route"],"incomplete");self.assertIsNone(d["needs_review"])
