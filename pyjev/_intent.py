"""Speech act of the mentioned instruction; a signal is never removed from the audit record.
Only the outer linguistic frame is used by the new head. No remote services or side effects.
"""
from collections import Counter
from hashlib import blake2b
import math
import re
import unicodedata

LABELS=("mention","act","unclear")
THRESHOLDS=(.50,.60,.70,.80,.90)
MARK="◊"
OPEN={"“":"”","「":"」","『":"』","‘":"’","《":"》",'"':'"'}
CLOSE=set(OPEN.values())
def norm(v):
    return unicodedata.normalize("NFKC",v).casefold().replace(MARK," ")

def outside(t):
    out=[];stack=[];spans=0;bad=False;max_depth=0
    for ch in t:
        if stack and ch==stack[-1]:stack.pop();continue
        if ch in OPEN:
            if not stack:out.append(" "+MARK+" ");spans+=1
            stack.append(OPEN[ch]);max_depth=max(max_depth,len(stack))
        elif ch in CLOSE:bad=True
        elif not stack:out.append(ch)
    return re.sub(r"[^\S\n]+"," ","".join(out)).strip(),spans,(bad or bool(stack)),max_depth

EDITOR=re.compile(r"解[释读]|阐释|分析|转述|复述|翻[译成]|译[成法稿文]|校[对订译]|审[稿校]|润色|改写|改[为成].{0,6}(?:句|语|写法|说法)|拟.{0,7}(?:题|导语)|起.{0,4}标题|配.{0,5}(?:标题|说明)|加.{0,5}标题|比较.{0,15}(?:写法|说法|区别)|评[述析价语]|点评|断句|词义|用词|措辞|语气|拼写|语法|标点|含义|什么意思|什么意[思义]|想表达|怎么理解|如何表[达述]|如何理解|拗口|读起来|是否自然|是不是.{0,3}(?:句|问法)|(?:检查|校核).{0,8}文字|summari[sz]e|translate|paraphrase|proofread|rephrase|wording|what does .{1,24} mean",re.I)
OBJECT=re.compile(r"原[话句文稿意]|例[句文子]|引[句文语述号]|句[式子]|这[段句话行]|这[一条]句|表[达述]|措辞|术语|标[点题]|语[气法义]|文本|译[稿者文]|文[档章稿字]|课[件文程]|教材|讲[稿义]|章节|段落|课本|导语|培训|海报|台词|来信|备忘录|quote|sentence|wording|article|passage|phrase")
QUESTION=re.compile(r"请|帮|能否|是否|是不是|如何|怎么|什么|想知道|只[看谈需]|[?？]|编辑|审稿|课[件堂]|例句|阅读|please|what does|could you")
EDITOR_IMPER=re.compile(r"请|帮|只|仅|替|想|需要|(?:翻译|改写|校对|转述|润色|阅读题|拟标题|解释|解读|指出|审稿|审校|写评语)")
UNCLEAR=re.compile(r"不确定|谁来|由谁|没有.{0,5}(?:定论|交代|决定|写由|上下文|说明意图)|没(?:写|想好)|尚未|待(?:定|补|确认|核实|对方|进一步|批准)|用途不[明详]|未[定知明]|可能.{0,8}(?:示例|例子|任务|用途)|会不会|是否(?:要|应该|需要|获准|真的执行)|不知道(?:是否|该不该)|拿不准|等.{0,4}确认|没有结论|purpose unclear")
ACTION_PH=r"执行|实行|实施|照[此着原样]?做|照.{0,5}(?:办|行动)|落实|办理|办[妥完好]|动手|付诸(?:行动|实施)|实际(?:操作|完成|处理|照做)|按.{0,10}(?:要求|原文|内容|指令|引文|原话|这句|此|里面).{0,6}(?:做|操作|处理|行动)|把.{0,12}(?:事情|里面的事|这个事项|任务|事项).{0,4}(?:做完|办好|完成)|交(?:回|还|付|出).{0,4}(?:成品|结果)|do what it says|carry (?:it|this) out|perform (?:the|this) (?:task|action)"
ACTION=re.compile(ACTION_PH)
# Limited negation: remove an explicitly negated action, never a whole clause or arbitrary following words.
NEG_ACT=re.compile(r"(?:无需|不必|不用|不要|不是让|并非让|没有要求|别|无须)(?:你|去|实际|真的|再|直接|亲自|也|再去|照着){0,3}(?:"+ACTION_PH+r")")
NO_GUESS=re.compile(r"不要以为|并非不能|不能不|不得不|不是不|不要不|并非不用|未必不用")
PIVOT=re.compile(r"(?:另外|此外|随后|接着|然后|再者|同时还|而且还|另请|并请|不过还|但是还|但现在|but also|then also)")
ASK=re.compile(r"请|你(?:来|要|去|负责|现在|必须)|交给(?:你|助手)|需要你|务必|动手|照做|我想让|替我|帮我|please|you must|go ahead")
TASK=re.compile(r"整理|排列|排序|归类|归档|编号|登记|贴|核对|保存|发送|更[新改]|搬|放到|制作|写进|抄下|列出|生成|操作|处理|提交|把.{1,12}(?:分|排|存|放)|交给|send|save|change")
COMPLEX=re.compile(r"\x00|\x1b|[\u202a-\u202e\u2066-\u2069]|\x60{3}|(?:^|\n)\s*(?:system|assistant|tool|developer)\s*[:：]|</?[a-z][^<>\n]{0,100}>",re.I)
def frame(text):
    if not isinstance(text,str) or not text.strip() or len(text)>32768:return None
    t=norm(text);s,spans,bad,depth=outside(t)
    pieces=[p.strip() for p in re.split(r"[。；;！!？?，,\n]+",s) if p.strip()]
    what=bool(EDITOR.search(s));obj=bool(spans or OBJECT.search(s))
    maybe=bool(UNCLEAR.search(s) or NO_GUESS.search(s))
    # Asking about the word "execute" is not an instruction. Imperatives with a separate action take priority.
    affirmative=NEG_ACT.sub(" ",s)
    direct=bool(ACTION.search(affirmative))
    follow=bool(PIVOT.search(affirmative) and any(TASK.search(q) and not EDITOR.search(q) for q in pieces))
    additional=any(ASK.search(p) and TASK.search(p) and not EDITOR.search(p) for p in pieces)
    # A bare purpose claim, a bare quote, or executable-looking mixed markup is never a reason to suppress review.
    blocked=bool(bad or depth>3 or spans>4 or len(t)>650 or len(pieces)>8 or t.count("\n")>2 or COMPLEX.search(t))
    if not spans and (":" in s or "\n" in s) and re.search(r"[:\n].{5,}",s):blocked=True
    scope=bool(what and obj and (QUESTION.search(s) or EDITOR_IMPER.search(s)) and not additional)
    return {"outer":s,"quoted":bool(spans),"object":obj,"editor":what,"scope":scope,"maybe":maybe,
            "direct":direct,"follow":follow,"request":bool(ASK.search(s)),"task":bool(TASK.search(s)),
            "additional":additional,"blocked":blocked,"negated":affirmative!=s}

def feats(f):
    # No inner text, raw source, carrier, model score, IDs or labels are features of the intent model.
    compact=re.sub(r"[^a-z0-9\u3400-\u9fff◊]+"," ",f["outer"]).strip()
    bag={}
    for w in compact.split():
        for k in (1,2,3):
            for i in range(len(w)-k+1):bag["n:"+w[i:i+k]]=1.
    for k in ("quoted","object","editor","scope","maybe","direct","request","task","follow","additional","blocked","negated"):
        if f[k]:bag["s:"+k]=4.
    return {blake2b(k.encode(),digest_size=12).hexdigest():v for k,v in bag.items()}

def adjudicate(f,p,threshold):
    if not f or f["blocked"] or f["maybe"]:return "unclear"
    if f["direct"] or f["follow"]:return "act"
    if f["additional"] and p[1]>=.5:return "act"
    if threshold is not None and f["scope"] and p[0]>=threshold and p[0]>max(p[1:]):return "mention"
    if f["request"] and not f["scope"] and f["task"] and p[1]>=.65 and p[1]>p[2]:return "act"
    return "unclear"

class Head:
    def __init__(self,book):
        if book["format"]!="nuwa-mention-head-v1" or tuple(book["classes"])!=LABELS or book["tau"] not in (*THRESHOLDS,None):
            raise ValueError("invalid speech-act model")
        self.tau=book["tau"];self.bias=book["bias"];self.table={k:(idf,weights) for k,idf,weights in book["features"]}
        if not (len(self.bias)==3 and all(math.isfinite(x) for x in self.bias) and 0<len(self.table)==len(book["features"])<=10000
                and all(len(w)==3 and all(math.isfinite(x) for x in w) and math.isfinite(i) and i>=1 for i,w in self.table.values())):
            raise ValueError("invalid weights")
    def state(self,text):
        f=frame(text)
        if not f:return "unclear"
        vals=[(v*self.table[k][0],self.table[k][1]) for k,v in feats(f).items() if k in self.table]
        n=math.sqrt(math.fsum(v*v for v,w in vals)) or 1.
        z=[b+math.fsum(v*w[i] for v,w in vals)/n for i,b in enumerate(self.bias)];mx=max(z)
        ex=[math.exp(a-mx) for a in z];p=[a/sum(ex) for a in ex]
        return adjudicate(f,p,self.tau)

def disposition(old_signal,intent):
    if old_signal is None:return "incomplete"
    if not old_signal:return "no_signal"
    return "record_only" if intent=="mention" else "review"
