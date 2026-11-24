"""Immutable artifact catalog, data-only IO and canonical receipts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / "sources.json").read_text())
PYJEV = "b0d755fd2a3265f70bb4241b7126a3887035362d"
HIKMA = "b7d8317a617012d23713f4999acaba0690bc1c73"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def filehash(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def checked(root, name):
    p = Path(root) / name
    if filehash(p) != CATALOG[name]["sha256"]:
        raise ValueError("pinned artifact mismatch: " + name)
    return p

def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def jsonl(path):
    with Path(path).open(encoding="utf8") as f:
        for line in f:
            yield json.loads(line)

def save_rows(path, rows):
    with Path(path).open("x", encoding="utf8", newline="\n") as f:
        for row in rows:
            f.write(wire(row) + "\n")

def save_json(path, obj):
    with Path(path).open("x", encoding="utf8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
