"""Acquire pinned public data as inert bytes. Never import, execute or serve downloaded files."""
import argparse,hashlib,json,re,subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from .prepare import INDEX
class Scripts(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.objects=[]
    def handle_starttag(self,t,attrs):
        if t=="script":self.active=dict(attrs).get("type","").lower()=="application/ld+json"
    def handle_endtag(self,t):
        if t=="script":self.active=False
    def handle_data(self,s):
        if self.active:
            val=json.loads(s)
            self.objects.extend(val if isinstance(val,list) else [val])
def source_bytes(info,is_article):
    url=info["url"]
    if urlsplit(url).scheme!="https" or urlsplit(url).hostname not in {"huggingface.co","raw.githubusercontent.com","aithreat.io"}:
        raise ValueError("unexpected origin")
    # Only authored source URLs/redirects over HTTPS. No auth, no shell, no scripts from sources.
    cp=subprocess.run(["curl","-qfsSL","--proto","=https","--proto-redir","=https",
                       "--max-time","75","--retry","1","--max-filesize","10000000",url],capture_output=True,check=True)
    blob=cp.stdout
    if is_article:
        page=Scripts();page.feed(blob.decode("utf8"))
        obj=next(x for x in page.objects if isinstance(x,dict) and x.get("@type")=="Article")
        if obj.get("inLanguage")!="zh" or obj.get("datePublished")!=info["date"] or obj.get("license")!="https://creativecommons.org/licenses/by/4.0/":
            raise ValueError("article metadata changed")
        blob=obj["description"].encode("utf8")
    return blob
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--data",type=Path,required=True);a=p.parse_args()
    a.data.mkdir(exist_ok=True,parents=True)
    for name,item in INDEX.items():
        if not re.fullmatch(r"[-a-zA-Z0-9]+\.(?:mdx?|jsonl|parquet|article|py)",name):raise ValueError("invalid local filename")
        out=a.data/name;exists=out.exists()
        blob=out.read_bytes() if exists else source_bytes(item,name.endswith(".article"))
        if hashlib.sha256(blob).hexdigest()!=item["sha256"]:raise ValueError("pinned source unavailable or changed: "+name)
        if not exists:
            with out.open("xb") as f:f.write(blob)
    print("Verified",len(INDEX),"source artifacts; no code from the sources was executed.")
if __name__=="__main__":main()
