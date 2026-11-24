"""Bounded, non-executing text views. No HTML/Markdown rendering, imports or URL fetches."""
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
import unicodedata

MAX=32768
SPACE=re.compile(r"[\t \f\v]+")
_SPLIT=re.compile(r"[。！？!?；;\n]+")
_HTML=re.compile(r"<(?:html|body|div|article|section|main|p|table|aside|span|li)(?:\s|>)",re.I)
OPEN={'“':'”','「':'」','『':'』','‘':'’','"':'"','`':'`'}
CLOSE=set(OPEN.values())

class _Visible(HTMLParser):
    """Keep text, never run the document. Presence/visibility is not a verdict."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
    def handle_data(self,data):
        self.parts.append(data)
    def handle_comment(self,data):
        # Untrusted tool consumers sometimes see comments as well.
        self.parts.extend(["\n",data,"\n"])
    def handle_starttag(self,tag,attrs):
        if tag in {"p","div","body","li","tr","aside","section","article","br"}:
            self.parts.append("\n")
        for key,value in attrs:
            if value and key in {"alt","title","aria-label"}:
                self.parts.extend(["\n",value,"\n"])
    def handle_endtag(self,tag):
        if tag in {"p","div","li","tr","article","section"}:self.parts.append("\n")

@dataclass(frozen=True)
class View:
    full:str
    outer:str
    quotes:int
    balanced:bool
    markup:bool
    clauses:tuple[str,...]

def split_quotes(text):
    outer=[];stack=[];count=0;ok=True
    for ch in text:
        if stack and ch==stack[-1]:
            stack.pop()
            if not stack:outer.append(" ")
        elif ch in OPEN:
            if len(stack)==12:
                ok=False
            else:
                if not stack:outer.append(" 【引文】 ");count+=1
                stack.append(OPEN[ch])
        elif ch in CLOSE:
            ok=False
            if not stack:outer.append(ch)
        elif not stack:outer.append(ch)
    return SPACE.sub(" ","".join(outer)),count,ok and not stack

def view(s):
    if not isinstance(s,str) or not s.strip() or len(s)>MAX or any(0xd800<=ord(c)<=0xdfff for c in s):
        return None
    s=unicodedata.normalize("NFKC",s).casefold()
    markup=bool(_HTML.search(s))
    if markup:
        html=_Visible()
        try:html.feed(s);html.close()
        except (ValueError,AssertionError):return None
        s=" ".join(html.parts)
    s=SPACE.sub(" ",s).strip()
    out,n,ok=split_quotes(s)
    return View(s,out,n,ok,markup,tuple(p.strip() for p in _SPLIT.split(out) if p.strip()))
