"""Check the documented Chinese examples through native CLIs and the human-readable view. No dependencies."""
import json
from pathlib import Path
import subprocess
import sys

from examples.audit_zh import explain

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "audit-output.json"


def check():
    rows = json.loads(EXAMPLES.read_text(encoding="utf8"))
    checked = 0
    for row in rows:
        for engine, candidate in (("v010", False), ("scope1", True)):
            expected = row[engine]
            via_json = ["-m", "examples.audit_zh"] + (["--scope"] if candidate else [])
            native = (["-m", "candidates.scope1", "--json"] if candidate
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
    return len(rows), checked


if __name__ == "__main__":
    examples, outputs = check()
    print(f"OK: {examples} examples, 2 frozen detectors, {outputs} CLI checks (native JSON, translated JSON, Chinese view).")
