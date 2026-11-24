"""Pure Python post-response detector. No actions, HTTP, logging or model dependency."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import math
import re
import unicodedata

LIMIT=32768
VERSION="nuwa-bilingual-postsignal-linear-1"
HAN=r"\u3400-\u9fff\uf900-\ufaff"
PIECES=re.compile("["+HAN+"]|[^\\W\\d_"+HAN+"]+|#")
LEGACY=re.compile(r"[^\W\d_]+|#")
HEX32=re.compile(r"[0-9a-f]{32}\Z")
HEX64=re.compile(r"[0-9a-f]{64}\Z")

def normalized(t):return re.sub(r"\d+","#",unicodedata.normalize("NFKC",t).casefold())
def units(t):return tuple(PIECES.findall(normalized(t)))
def termhash(t):return hashlib.sha256(t.encode()).hexdigest()
def fhash(t):return hashlib.blake2b(t.encode(),digest_size=16).hexdigest()

def legacy_terms(t):
    return {termhash(w) for w in set(LEGACY.findall(normalized(t))) if len(w)>=3}

def counts(t):
    u=units(t);f=Counter("w:"+w for w in u)
    f.update("p:"+a+" "+b for a,b in zip(u,u[1:]))
    # Split Han units, not whole Chinese clauses; keep word-internal contexts for alphabetic text.
    f.update("t:"+"".join(x) for x in zip(u,u[1:],u[2:])
             if all(len(w)==1 and ("\u3400"<=w<="\u9fff" or "\uf900"<=w<="\ufaff") for w in x))
    for w,n in Counter(u).items():
        if len(w)<2:continue
        piece=" "+w+" "
        for k in (3,4,5):
            for j in range(len(piece)-k+1):f["c:"+piece[j:j+k]]+=n
    return {fhash(k):v for k,v in f.items()}

def eligible(text):return isinstance(text,str) and bool(text.strip()) and len(text)<=LIMIT
def anchor(keys,lex):return len(keys.intersection(lex))>=2

@dataclass
class Detector:
    english:frozenset
    bilingual:frozenset
    weights:dict
    intercept:float
    threshold:float|None

    @classmethod
    def parse(cls,d):
        if not (d.get("format")==VERSION and type(d.get("round")) is int and 0<=d["round"]<=1000
                and ((d["round"]==0 and d.get("threshold") is None) or
                     (d["round"]>0 and d.get("threshold") in (0.,.5,1.,1.5,2.,3.)))):raise ValueError("invalid contract")
        a,b,fs=d["english"],d["bilingual"],d["features"]
        if not all(isinstance(x,list) and len(set(x))==len(x) and all(HEX64.fullmatch(k) for k in x) for x in (a,b)):
            raise ValueError("invalid anchor vocabulary")
        if not isinstance(fs,list) or not 0<len(fs)<=16000 or not math.isfinite(d["intercept"]):raise ValueError("bad dimensions")
        table={}
        for k,idf,w in fs:
            if not HEX32.fullmatch(k) or k in table or not (math.isfinite(idf) and idf>=1 and math.isfinite(w)):
                raise ValueError("invalid learned predicate")
            table[k]=(idf,w)
        return cls(frozenset(a),frozenset(b),table,d["intercept"],d["threshold"])

    def evidence(self,text):
        if not eligible(text):return None
        keys=legacy_terms(text);a=anchor(keys,self.english);b=anchor(keys,self.bilingual)
        weighted=[((1+math.log(c))*self.weights[k][0],self.weights[k][1])
                  for k,c in counts(text).items() if k in self.weights]
        norm=math.sqrt(math.fsum(x*x for x,w in weighted))
        score=self.intercept+(math.fsum(x*w for x,w in weighted)/norm if norm else 0)
        hit=self.threshold is not None and score>=self.threshold
        return a,b,score,a or b or hit

    def report(self,text):
        e=self.evidence(text)
        return {"signal":("unknown" if e is None else "suspected" if e[-1] else "no_signal"),
                "service_action":"none","model_identity":"not_evaluated","probability":None}
