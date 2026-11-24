"""Build the offline English reader from its two source chapters (editor-only dependencies).
Install markdown-it-py==3.0.0 and beautifulsoup4==4.15.0; run python -m research.render_handbook [--check].
No remote assets, external requests or scripts, and no runtime dependency for either auditor.
"""
import argparse
import base64
from html import escape
from pathlib import Path
import re

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from research.render_audit_tables import evidence_tables

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CHAPTERS = {"audit-study.md": "research", "start-local.md": "guide"}
GUIDE_SECTIONS = ("deploy", "usage", "examples")
CSS = """
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f7f8f5;color:#17323a;font:16px/1.7 system-ui,sans-serif}
main{max-width:980px;margin:auto;padding:30px min(5vw,54px) 65px;background:#fff}
header{border-bottom:2px solid #28616d;padding-bottom:12px}header b{font-size:1.25rem;color:#104752}nav{display:flex;flex-wrap:wrap;gap:.2em 1em}nav a{white-space:normal}
h1{font-size:clamp(1.65rem,4vw,2.35rem);line-height:1.25;margin:1.3em 0 .55em}h2{font-size:1.3rem;line-height:1.4;margin:1.6em 0 .5em}
a{color:#075875;text-underline-offset:.18em}b,strong{color:#132e38}table{border-collapse:collapse;width:100%;font-size:.91rem}
table{margin:.8em 0 1.1em;border-top:2px solid #273336;border-bottom:2px solid #273336;font-variant-numeric:tabular-nums}
th,td{padding:.52em .68em;text-align:left;vertical-align:top}thead{border-bottom:1px solid #273336}th{color:#1a3038;font-weight:650}caption{text-align:left;font-size:1.08em;font-weight:700;margin-bottom:.45em}
.evidence th:not(:first-child),.evidence td:not(:first-child){text-align:center;white-space:nowrap}.tablenote{font-size:.92em;color:#40545c;margin-top:-.55em}
pre{background:#f0f4f3;padding:.8em 1em;overflow:auto}code{font: .89em/1.65 ui-monospace,monospace;overflow-wrap:anywhere}
section+section{border-top:2px solid #becdc9;margin-top:2.5rem}footer{border-top:1px solid #dce5e4;margin-top:2em;padding-top:1em}
@media(max-width:650px){main{padding:12px 14px 35px}table{display:block;overflow-x:auto}pre{font-size:.87rem}}
@media print{body{background:white}main{max-width:none}header nav,footer{display:none}img,table,pre{break-inside:avoid}a{color:inherit}}
"""

def embed(path, mimetype):
    return "data:" + mimetype + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")

def render():
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    specs = {item[0]: item for item in evidence_tables()}
    chapters = []
    for filename, slug in CHAPTERS.items():
        src = (DOCS / filename).read_text(encoding="utf-8")
        markers = re.findall(r'^<a id="([a-z-]+)"></a>$', src, re.M)
        src = re.sub(r'^<a id="[a-z-]+"></a>$', "", src, flags=re.M)
        soup = BeautifulSoup(md.render(src), "html.parser")
        soup.h1["id"] = slug
        if slug == "guide":
            assert tuple(markers) == GUIDE_SECTIONS
            for heading, anchor in zip(soup.find_all("h2"), GUIDE_SECTIONS):
                heading["id"] = anchor
        if slug == "research":
            assert markers == ["paired-results"]
            soup.find_all("h2")[3]["id"] = markers[0]
        for tag in soup.find_all("img"):
            path = (DOCS / tag["src"]).resolve()
            if path.parent != DOCS / "tables" or path.suffix != ".svg" or path.stem not in specs:
                raise ValueError("unexpected image")
            key, title, subtitle, heads, rows, note = specs[path.stem]
            cols = "".join('<th scope="col">'+escape(c)+'</th>' for c in heads)
            body = "".join("<tr>" + "".join("<td>"+escape(str(c))+"</td>" for c in row) + "</tr>" for row in rows)
            fragment = BeautifulSoup('<div><table class="evidence" id="'+key+'"><caption>'+escape(title)+
                                     '</caption><thead><tr>'+cols+'</tr></thead><tbody>'+body+
                                     '</tbody></table><p class="tablenote">'+escape(subtitle+" "+note)+'</p></div>', "html.parser")
            wrapper = tag.parent if tag.parent.name == "p" and len(tag.parent.contents) == 1 else tag
            wrapper.replace_with(fragment.div)
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith(("https://", "#")):
                continue
            name, _, fragment = href.partition("#")
            if name in CHAPTERS and (not fragment or fragment in GUIDE_SECTIONS):
                link["href"] = "#" + (fragment or CHAPTERS[name])
                continue
            path = (DOCS / name).resolve()
            if ROOT not in path.parents or path.suffix not in (".json", ".md"):
                raise ValueError("unexpected supplement: " + name)
            link["href"] = embed(path, "application/json" if path.suffix == ".json" else "text/markdown")
            link["download"] = path.name
        chapters.append("<section>" + str(soup) + "</section>")
    title = escape("pyjev_v1 | Post-response AI gateway auditing")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<title>' + title + '</title><style>' + CSS + '</style></head><body><main>'
            '<header><b>' + title + '</b><nav aria-label="Contents">'
            '<a href="#research">Research</a><a href="#deploy">Deployment</a><a href="#usage">Usage</a><a href="#examples">Outputs and examples</a>'
            '</nav></header>' + ''.join(chapters) +
            '<footer>Text and tables are available offline. External references require a connection. '
            '<a href="https://github.com/123yjf/pyjev_ai_security">GitHub repository</a></footer></main></body></html>\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = DOCS / "pyjev_v1.html"
    content = render().encode("utf-8")
    if args.check:
        if not target.exists() or target.read_bytes() != content:
            raise SystemExit("Offline handbook is stale; run python -m research.render_handbook")
    else:
        target.write_bytes(content)
    print("Offline handbook:", len(content), "bytes; 2 chapters")

if __name__ == "__main__":
    main()
