"""Read one UTF-8 text from stdin. Never echo, persist or execute the input."""
import argparse
import json
import sys

from pyjev.api import ModelIntegrityError
from . import Auditor, MODEL_ID
from .explain import explain, explain_en
from .view import MAX


def main(argv=None):
    parser = argparse.ArgumentParser(prog=MODEL_ID, description=__doc__)
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="native audit JSON (default)")
    fmt.add_argument("--explain", "--en", action="store_true", help="four-line English interpretation")
    fmt.add_argument("--zh", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--version", action="version", version=MODEL_ID)
    args = parser.parse_args(argv)
    buf = sys.stdin.buffer.read(4 * MAX + 1)
    try:
        text = buf.decode("utf-8", "strict") if len(buf) <= 4 * MAX else None
    except UnicodeDecodeError:
        text = None
    try:
        result = Auditor().audit(text)
    except ModelIntegrityError:
        print("Model integrity check failed; no audit decision.", file=sys.stderr)
        return 1
    data = result.as_dict()
    print(explain_en(data) if args.explain else explain(data) if args.zh else json.dumps(data, ensure_ascii=False, sort_keys=True))
    return 2 if result.needs_review is None else 0


if __name__ == "__main__":
    raise SystemExit(main())
