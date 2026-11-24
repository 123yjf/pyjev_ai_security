"""Export the paired study's English publication tables to an explicit directory."""
import argparse
from pathlib import Path
from research.render_audit_tables import evidence_tables, svg

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    for item in evidence_tables():
        (out / (item[0] + ".svg")).write_bytes(svg(*item).encode("utf-8"))

if __name__ == "__main__":
    main()
