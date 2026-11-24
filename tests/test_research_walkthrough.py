"""Contract of the review material; never modify or train the two detectors from these examples."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from candidates.scope1 import ScopeAuditor
from examples.audit_zh import explain
from pyjev import Auditor
from research.footprint.measure import percentile

ROOT = Path(__file__).resolve().parents[1]


def artifact(name):
    return json.loads((ROOT / name).read_text(encoding="utf8"))


class ResearchWalkthroughTests(unittest.TestCase):
    def test_setup_never_overwrites_an_existing_environment(self):
        script = ROOT / "research/footprint/venv311.sh"
        with tempfile.TemporaryDirectory() as directory:
            cp = subprocess.run(["sh", str(script), "runtime", directory], capture_output=True)
            self.assertEqual(cp.returncode, 2)
            self.assertIn(b"never overwritten", cp.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_documented_examples_are_the_two_native_results(self):
        base, candidate = Auditor(), ScopeAuditor()
        rows = artifact("examples/audit-output.json")
        self.assertEqual([x["id"] for x in rows], ["explain", "act", "reported_incident", "blank"])
        guide = (ROOT / "docs/start-local.md").read_text(encoding="utf8")
        for row in rows:
            with self.subTest(id=row["id"]):
                self.assertEqual(row["v010"], base.audit(row["text"]).as_dict())
                self.assertEqual(row["scope1"], candidate.audit(row["text"]).as_dict())
                for name in ("v010", "scope1"):
                    lines = explain(row[name]).splitlines()
                    self.assertEqual([s.split("：", 1)[0] for s in lines], ["文字意图", "注入线索", "复核建议", "实际动作"])
                    if row["text"].strip():
                        self.assertNotIn(row["text"], "\n".join(lines))
        case = rows[2]["scope1"]
        self.assertIn(explain(case), guide)
        self.assertEqual(json.loads(re.search(r"~~~json\n(.*?)\n~~~", guide, re.S).group(1)), case)
        self.assertIsNone(rows[3]["scope1"]["needs_review"])

    def test_resource_table_matches_frozen_measurements(self):
        data = artifact("research/footprint/observed-m4.json")
        article = (ROOT / "docs/audit-study.md").read_text(encoding="utf8")
        self.assertEqual(data["unique_inputs"], 924)
        self.assertEqual(data["fresh_processes"], 9)
        for key, label in (("v010", "PyJev v0.1.0"), ("scope", "Scope-1"), ("hikma", "HikmaAI INT8／CPU")):
            d = data["engines"][key]
            self.assertEqual([x["n"] for x in d["rounds"]], [924] * 3)
            self.assertEqual(d["timed"], 3 * 924)
            self.assertIn(f'| {label} | {d["p50_ms"]:.3f} | {d["p95_ms"]:.3f} | '
                          f'{d["process_cpu_ms_per_text"]:.3f} | {d["maximum_process_peak_rss_mib"]:,.1f} |', article)
        self.assertEqual(percentile([9, 3, 1, 6], 0.5), 3)
        self.assertEqual(percentile([9, 3, 1, 6], 0.95), 9)

    def test_accuracy_and_resource_replays_used_identical_inputs(self):
        cost = artifact("research/footprint/observed-m4.json")
        run = artifact("research/footprint/replay-receipt.json")
        seal = artifact("research/scope_study/cohort.json")
        trace = artifact("research/scope_study/prediction-receipt.json")
        self.assertEqual(run["inputs_sha256"], cost["inputs_sha256"])
        self.assertEqual(run["inputs_sha256"], seal["inputs_sha256"])
        self.assertEqual(run["gold_sha256"], seal["gold_sha256"])
        self.assertEqual(run["predictions_sha256"], trace["predictions_sha256"])
        self.assertTrue(run["full_aggregate_matches_reference"])
        self.assertTrue(run["prediction_bytes_match_reference"])
        self.assertFalse(run["reused_prior_predictions"])
        self.assertEqual(run["regenerated_inputs"], cost["unique_inputs"])
        self.assertEqual(sum(x.get("verified_cache", 0) for x in run["asset_counts"].values()), 44)

    def test_all_local_reader_links_resolve(self):
        for filename in ("README.md", "README.en.md", "docs/audit-study.md", "docs/start-local.md"):
            path = ROOT / filename
            content = path.read_text(encoding="utf8")
            for target in re.findall(r"\]\(([^\s)]+)\)", content):
                if "://" not in target and not target.startswith("#"):
                    with self.subTest(filename=filename, target=target):
                        self.assertTrue((path.parent / target.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
