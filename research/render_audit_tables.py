"""Render the paper's two three-rule tables from the sealed scores, without plotting dependencies."""
import argparse
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "tables"

def evidence_tables():
    result = json.loads((ROOT / "research/scope_study/blind-results.json").read_text(encoding="utf-8"))
    rows = []
    for key, label, error, denom in (
        ("tool_injected", "Injected tool responses", "fn", "positive"),
        ("tool_clean", "Clean web templates", "fp", "negative"),
        ("agent_task", "Ordinary tool tasks", "fp", "negative"),
        ("guide_discussion", "Instruction discussions", "fp", "negative"),
        ("guide_quote", "Quoted instructions", "fp", "negative"),
    ):
        g = result["groups"][key]
        rows.append((label, "Miss" if error == "fn" else "False alarm", g[denom],
                     *(g["modes"][model][error] for model in ("scope", "hikma"))))
    yield ("audit-errors", "Table 1. Missed injections and false alarms",
           "The two rightmost columns count errors. Lower is better.",
           ("Test material", "Error type", "Texts", "pyjev_v1", "HikmaAI"), rows,
           "Example: of 450 injected responses, pyjev_v1 missed 413; HikmaAI missed 71.")
    rows = []
    for key, label, answer in (("mention", "Discussion or quotation", "mention"),
                               ("act", "Request to act", "act"), ("ambiguous", "Indeterminate intent", "unclear")):
        g = result["intent"][key]
        correct = g["scope_speech"].get(answer, 0)
        rows.append((label, g["n"], correct, g["n"] - correct))
    yield ("intent-accuracy", "Table 2. Did pyjev_v1 recognize the speaker's intent?",
           "Correct predictions are counted against the human label.",
           ("Human label", "Texts", "Correct", "Other answers"), rows,
           "HikmaAI does not predict speaker intent; it is not scored on this task.")

def svg(name, title, subtitle, headers, rows, note):
    xs = (20, 335, 475, 607, 727) if len(headers) == 5 else (20, 425, 566, 715)
    bottom = 119 + 35 * len(rows)
    h = bottom + 49
    def word(x, y, s, *, size=18, weight=400, align="start"):
        return (f'<text x="{x}" y="{y}" text-anchor="{align}" font-size="{size}" '
                f'font-weight="{weight}">{escape(str(s))}</text>')
    def line(y, w):
        return f'<line x1="16" y1="{y}" x2="780" y2="{y}" stroke="#202a30" stroke-width="{w}"/>'
    def cells(y, row, head=False):
        return ''.join(word(x, y, v, size=18, weight=600 if head else 400,
                            align="start" if i == 0 else "middle") for i, (x, v) in enumerate(zip(xs, row)))
    alt = "; ".join(", ".join(map(str, row)) for row in rows)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="' + str(h) +
            '" viewBox="0 0 800 ' + str(h) + '" role="img" aria-labelledby="title desc">\n'
            '<title id="title">' + escape(title) + '</title><desc id="desc">' +
            escape(subtitle + " " + " / ".join(headers) + ": " + alt + ". " + note) + '</desc>\n'
            f'<rect width="800" height="{h}" fill="white"/><g fill="#202a30" '
            'font-family="system-ui, -apple-system, Arial, sans-serif">\n' +
            word(16,30,title,size=24,weight=650) + word(16,57,subtitle,size=16) +
            line(74,2.3) + cells(102,headers,True) + line(116,1.0) +
            ''.join(cells(143+35*i, row) for i, row in enumerate(rows)) +
            line(bottom,2.3) + word(16,bottom+31,note,size=16) + '</g></svg>\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        OUT.mkdir(parents=True, exist_ok=True)
    for item in evidence_tables():
        dest = OUT / (item[0] + ".svg")
        data = svg(*item).encode("utf-8")
        if args.check:
            if not dest.is_file() or dest.read_bytes() != data:
                raise SystemExit("Table out of date: " + dest.name)
        else:
            dest.write_bytes(data)
    print("2 three-rule tables match the frozen study scores.")

if __name__ == "__main__":
    main()
