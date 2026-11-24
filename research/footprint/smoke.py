"""Verify the published English examples and the original-language compatibility fixtures offline."""
import json
from pathlib import Path
import subprocess
import sys

from examples.audit_zh import explain
from pyjev_v1.explain import explain_en

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "audit-output.json"


def check():
    fixtures = ROOT / "tests/fixtures/discourse-regression.json"
    rows = json.loads(fixtures.read_text(encoding="utf8"))
    checked = 0
    for row in rows:
        for engine, candidate in (("v010", False), ("pyjev_v1", True)):
            expected = row[engine]
            via_json = ["-m", "examples.audit_zh"] + (["--v1"] if candidate else [])
            native = (["-m", "pyjev_v1", "--json"] if candidate
                      else ["-m", "pyjev", "scan", "-", "--json"])
            incomplete = expected.get("route", expected.get("review")) == "incomplete"
            for args, human, rc in ((native, False, 2 if candidate and incomplete else 0),
                                    (via_json + ["--json"], False, 2 if incomplete else 0),
                                    (via_json, True, 2 if incomplete else 0)):
                cp = subprocess.run([sys.executable, "-s", *args], input=row["text"].encode("utf8"),
                                    capture_output=True, cwd=ROOT, timeout=20)
                output = cp.stdout.decode("utf8")
                match = output.rstrip("\n") == explain(expected) if human else False
                if not human and output:
                    match = json.loads(output) == expected
                if cp.returncode != rc or not match or cp.stderr:
                    raise ValueError(f"example mismatch: {row['id']} / {engine} / {' '.join(args)} (exit {cp.returncode})")
                checked += 1
    public = json.loads(EXAMPLES.read_text(encoding="utf8"))
    for row in public:
        expected = row["pyjev_v1"]
        for args in (["--json"], ["--explain"]):
            cp = subprocess.run([sys.executable, "-s", "-m", "pyjev_v1", *args],
                                input=row["text"].encode("utf8"), capture_output=True, cwd=ROOT, timeout=20)
            actual = cp.stdout.decode("utf8").strip()
            match = json.loads(actual) == expected if args == ["--json"] else actual == explain_en(expected)
            if not match or cp.stderr or cp.returncode != (2 if expected["needs_review"] is None else 0):
                raise ValueError("Public example mismatch: " + row["id"])
            checked += 1
    return len(public), checked


if __name__ == "__main__":
    examples, outputs = check()
    print(f"OK: {examples} English examples; {outputs} CLI checks including compatibility regressions.")
