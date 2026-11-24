import hashlib
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from pyjev.api import _read
from pyjev.bench import replay_office
from pyjev.comparison import measured, compact
from research.render_report import render
ROOT=Path(__file__).resolve().parents[1]

class ReleaseEvidence(unittest.TestCase):
    def test_public_contract_matches_runtime_routes(self):
        from pyjev import Auditor
        from pyjev._office import exam
        a=Auditor();schema=json.loads((ROOT/"docs/audit.schema.json").read_bytes())
        self.assertFalse(schema["additionalProperties"])
        def matches(value, prop):
            if "enum" in prop:return value in prop["enum"]
            self.assertEqual(set(prop), {"const"})
            return type(value) is type(prop["const"]) and value==prop["const"]
        for text in [t for t,_,_ in exam()] + [""," "*4,"x"*32769]:
            result=a.audit(text).as_dict()
            self.assertEqual(set(result),set(schema["required"]))
            self.assertTrue(all(matches(result[k],prop) for k,prop in schema["properties"].items()))
            for rule in schema["allOf"]:
                if all(matches(result[k],v) for k,v in rule["if"]["properties"].items()):
                    self.assertTrue(all(matches(result[k],v) for k,v in rule["then"]["properties"].items()))

    def test_receipts_and_counts(self):
        d=measured()
        for name,protocol,script in (("pybot-comparison.json","fixtures/pybot-protocol-registered.utf8","compare_pybot.py"),
                                     ("pybot-raw-control.json","PYBOT_RAW_CONTROL.md","raw_control.py")):
            obj=_read(name)
            for k,f in (("protocol_sha256",protocol),("adapter_sha256",script)):
                self.assertEqual(obj[k],hashlib.sha256((ROOT/"research"/f).read_bytes()).hexdigest())
        expect={"office": {"mention":120,"act":120,"unclear":80},"external":{"injected":153,"benign":200},"legacy":{"injected":1323,"benign":61}}
        for sets in d.values():
            for s,row in sets.items():
                cm=row["confusion"]
                self.assertEqual({k:sum(v.values()) for k,v in cm.items()},expect[s])
                self.assertEqual(row["valid"],sum(r[p] for r in cm.values() for p in cm))
                self.assertEqual(row["correct"],sum(cm[g][g] for g in cm))
                if s!="office":
                    self.assertEqual(row["fpr_scored"],row["false_positives"]/row["valid_normals"] if row["valid_normals"] else None)
                    self.assertEqual(row["recall_scored"],row["true_positives"]/row["valid_positives"] if row["valid_positives"] else None)
        rows=compact()["rows"];self.assertEqual(len(rows),8)
        for row in rows:
            self.assertEqual(row["label_coverage"],row["valid"]/row["n"])
            self.assertEqual(row["correct_over_all"],row["correct"]/row["n"])
            if row["suite"]!="office":
                self.assertEqual(row["fpr_scored"],row["false_positives"]/row["valid_normals"] if row["valid_normals"] else None)
        self.assertEqual(d["pyjev"]["office"]["correct"],280)
        self.assertEqual(d["pyjev"]["external"]["true_positives"],61)
        self.assertEqual(d["pyjev"]["legacy"]["true_positives"],826)

    def test_report_and_worksheet_match(self):
        self.assertEqual(render(),(ROOT/"docs/comparison.md").read_text())
        self.assertEqual(replay_office()["demoted_discussion_cases"],{"n":3,"distinct_topics":1,"distinct_frames":3})
        controls=json.loads((ROOT/"research/signal-controls.json").read_bytes())
        gold=_read("results.json")
        for s,source in (("external",gold["new_external"]["full"]),("legacy",gold["old_chinese"]["comparison"])):
            for method,k in (("checkpoint_323","raw"),("experimental_routing","review")):
                for col,x in controls[s][method].items():self.assertEqual(x,source[k][col])

    def test_figures_are_static_vectors_and_referenced(self):
        report=(ROOT/"docs/comparison.md").read_text()
        for name in ("baselines","intent","false-reviews","detection"):
            rel="docs/figures/"+name+".svg"
            self.assertIn("figures/"+name+".svg",report)
            tree=ET.parse(ROOT/rel)
            self.assertFalse(any(el.tag.rsplit("}",1)[-1] in {"image","script","foreignObject"} for el in tree.iter()))

    def test_all_relative_docs_links(self):
        docs=(*sorted(ROOT.glob("*.md")),*sorted((ROOT/"docs").glob("*.md")),*sorted((ROOT/"research").glob("*.md")))
        for file in docs:
            for target in re.findall(r"\]\(([^#\s)]+?)(?:#[^)]*)?\)",file.read_text()):
                if target.startswith(("https:","http:","mailto:")):continue
                self.assertTrue((file.parent/target).is_file(),(file.name,target))

    def test_replay_uses_the_exact_registered_protocol_at_the_expected_path(self):
        # Do not hash a later reading copy as if it were the preregistration.
        from unittest.mock import patch
        from pathlib import Path as P
        import tempfile
        from research import run_original as runner
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            p = P(temp); data=p/"input"; data.write_bytes(b"fixture")
            expected=(runner.digest(b"fixture"), len(b"fixture"))
            got=[]
            def no_docker(cmd, **kwargs):
                got.extend(cmd)
                return SimpleNamespace(returncode=17,stdout=b"")
            with patch.dict(runner.os.environ,{"DOCKER_HOST":"unix:///test-only.sock"}), \
                 patch.dict(runner.SOURCES, {"external":expected,"legacy":expected}), \
                 patch.object(runner.subprocess,"check_output",return_value=runner.REV+"\n"), \
                 patch.object(runner.subprocess,"run",side_effect=no_docker):
                self.assertEqual(runner.main(["--upstream",temp,"--external",str(data),"--legacy",str(data),"--out",str(p/"result")]),17)
            mapping=next(x for x in got if "pybot-protocol-registered.utf8" in x)
            self.assertIn("/app/research/PYBOT_PROTOCOL.md", mapping)
            self.assertIn("ro",mapping)
            self.assertFalse((p/"result").exists())

    def test_cli_compare_is_frozen_report(self):
        from pyjev.cli import main
        from contextlib import redirect_stdout
        from io import StringIO
        out=StringIO()
        with redirect_stdout(out):self.assertEqual(main(["compare","--json"]),0)
        self.assertEqual(json.loads(out.getvalue()),compact())

if __name__=="__main__":unittest.main()
