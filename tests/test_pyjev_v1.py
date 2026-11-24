"""Public name, backwards compatibility, data minimisation and the standalone handbook."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import unittest
from xml.etree import ElementTree as ET

from research.render_audit_tables import evidence_tables, svg

from candidates.scope1 import ScopeAuditor
from pyjev import Auditor as DefaultAuditor
from pyjev_v1 import Auditor, MODEL_ID, audit
from pyjev_v1.explain import explain, explain_en

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/discourse-regression.json").read_text(encoding="utf-8"))

def cli(data, *args):
    return subprocess.run([sys.executable, "-m", "pyjev_v1", *args], input=data,
                          cwd=ROOT, capture_output=True, timeout=15)

class PublicInterface(unittest.TestCase):
    def test_frozen_default_and_explicit_v1_named_routes(self):
        self.assertIs(ScopeAuditor, Auditor)
        original, named = DefaultAuditor(), Auditor()
        self.assertEqual(MODEL_ID, "pyjev_v1")
        for row in CASES:
            with self.subTest(case=row["id"]):
                self.assertEqual(original.audit(row["text"]).as_dict(), row["v010"])
                self.assertEqual(named.audit(row["text"]).as_dict(), row[MODEL_ID])
                self.assertEqual(audit(row["text"]).as_dict(), row[MODEL_ID])

    def test_json_and_chinese_transcript_for_all_routes(self):
        version = cli(b"", "--version")
        self.assertEqual((version.stdout.strip(), version.returncode), (b"pyjev_v1", 0))
        for row in CASES:
            with self.subTest(case=row["id"]):
                inbound = row["text"].encode()
                raw, human = cli(inbound), cli(inbound, "--zh")
                code = 2 if row[MODEL_ID]["needs_review"] is None else 0
                self.assertEqual((raw.returncode, human.returncode), (code, code))
                self.assertEqual(json.loads(raw.stdout), row[MODEL_ID])
                self.assertEqual(human.stdout.decode().strip(), explain(row[MODEL_ID]))
                self.assertEqual((raw.stderr, human.stderr), (b"", b""))

    def test_invalid_streams_fail_without_echoing_content(self):
        for data in (b"", b"private-sentinel\xff", b"x"*32769, b"x"*131073):
            result = cli(data, "--json")
            self.assertEqual(result.returncode, 2)
            value = json.loads(result.stdout)
            self.assertEqual((value["route"], value["needs_review"]), ("incomplete", None))
            self.assertNotIn(b"private-sentinel", result.stdout + result.stderr)

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, name, attrs):
        self.tags.append((name, dict(attrs)))

class Handbook(unittest.TestCase):
    def test_downloadable_manual_contains_both_accessible_tables_and_no_external_resources(self):
        html = (ROOT / "docs/pyjev_v1.html").read_text(encoding="utf-8")
        p = Tags()
        p.feed(html)
        self.assertNotIn("Scope-1", html)
        self.assertNotIn("v0.1.0", html)
        self.assertNotRegex(html, r"[\u3400-\u9fff]")
        self.assertFalse(any(n in ("script", "iframe", "link", "object") for n, _ in p.tags))
        ids = {a["id"] for _, a in p.tags if "id" in a}
        self.assertTrue({"research", "guide", "deploy", "usage", "examples"} <= ids)
        for n, attrs in p.tags:
            if n == "a" and attrs.get("href", "").startswith("#"):
                self.assertIn(attrs["href"][1:], ids)
        self.assertFalse(any(n == "img" for n, _ in p.tags))
        self.assertEqual([a["id"] for n, a in p.tags if n == "table" and a.get("class") == "evidence"],
                         ["audit-errors", "intent-accuracy"])
        self.assertTrue({"audit-errors", "intent-accuracy", "paired-results"} <= ids)

    def test_current_reading_path_is_english_and_has_no_legacy_version_label(self):
        for rel in ("README.md", "README.en.md", "MODEL_CARD.md", "docs/audit-study.md", "docs/start-local.md",
                    "docs/scope-blind.md", "docs/contract.md", "docs/tables/audit-errors.svg", "docs/tables/intent-accuracy.svg",
                    "research/footprint/README.md", "examples/audit-output.json"):
            with self.subTest(path=rel):
                text = (ROOT/rel).read_text(encoding="utf-8")
                self.assertNotRegex(text, r"[\u3400-\u9fff]")
                self.assertNotIn("Scope-1", text)
                self.assertNotIn("v0.1.0", text)

    def test_paper_tables_have_exact_counts_and_only_three_rules(self):
        report = (ROOT / "docs/audit-study.md").read_text(encoding="utf-8")
        for item in evidence_tables():
            name, _, _, _, rows, _ = item
            table = ROOT / "docs/tables" / (name + ".svg")
            content = table.read_text(encoding="utf-8")
            self.assertEqual(content, svg(*item))
            self.assertEqual(len(ET.fromstring(content).findall(".//{*}line")), 3)
            self.assertIn("tables/" + table.name, report)
            if name == "audit-errors":
                self.assertEqual(rows[0][2:], (450, 413, 71))
                self.assertEqual(rows[2][2:], (401, 4, 36))
            else:
                self.assertEqual([r[1:] for r in rows], [(48, 18, 30), (21, 8, 13), (3, 3, 0)])

if __name__ == "__main__":
    unittest.main()
