"""Project-native terminal UI. All inputs are inert; only the explicit CLI controls the shell UI."""
import argparse
import json
from pathlib import Path
import random
import sys
from . import __version__
from .api import Auditor, ModelIntegrityError, _read
from .bench import replay_office
from .practice import GLOSS, describe, triplet

MAX_WIRE = 262144
HELP = "/help 指令  /demo 意图对照  /quiz 意图练习  /reset 清本次计数  /exit 离开"

def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, separators=(",",":"), allow_nan=False))

def one(a, text, machine=False):
    r = a.audit(text)
    if machine: emit(r.as_dict())
    else: print(describe(r))

def bounded_lines(stream):
    """Yield a single record or a size error. Drain huge records without allocating them."""
    while True:
        buf = stream.readline(MAX_WIRE + 2)
        if not buf: break
        body = buf.removesuffix(b"\n").removesuffix(b"\r")
        if len(body) > MAX_WIRE or (not buf.endswith(b"\n") and len(buf) == MAX_WIRE + 2):
            while buf and not buf.endswith(b"\n"):
                buf = stream.readline(MAX_WIRE + 2)
            yield None, "wire_limit"
        else:
            try: yield body.decode("utf-8"), None
            except UnicodeDecodeError: yield None, "invalid_utf8"

class DuplicateField(ValueError):
    pass

def unique_fields(pairs):
    values = {}
    for k,v in pairs:
        if k in values: raise DuplicateField()
        values[k] = v
    return values

def batch(a, stream, jsonl):
    failed = False
    for i, (text, error) in enumerate(bounded_lines(stream), start=1):
        if error is None and jsonl:
            try:
                v = json.loads(text, object_pairs_hook=unique_fields)
                if not isinstance(v,dict) or set(v) != {"text"} or not isinstance(v["text"],str):
                    error = "expected_text_object"
                else: text = v["text"]
            except DuplicateField: error = "duplicate_field"
            except (ValueError, RecursionError): error = "invalid_json"
        if error is not None:
            emit({"line":i,"error":error}); failed = True
        else: emit({"line":i,"audit":a.audit(text).as_dict()})
    return 2 if failed else 0

def demo(a):
    for i,(text, gold) in enumerate(triplet(), start=1):
        print(f"\n{i}  {text}\n   标注：{gold}\n   {describe(a.audit(text))}")
    text="收件人是志愿者，不是你。我只想听你点评「给提示注入公开课的章节配一个标题」的措辞。"
    print(f"\n额外对照（正常教学文本）：{text}\n{describe(a.audit(text))}")

def quiz(a, seed=7, rounds=3):
    deck = [case for topic in (0,2,4) for case in triplet(topic)]
    random.Random(seed).shuffle(deck); score = answered = 0
    print("语用意图自测｜1 讨论、2 要求落实、3 不确定。按 q 退出。")
    names = {"1":"mention","2":"act","3":"unclear"}
    for text, gold in deck[:rounds]:
        print(text)
        while True:
            try: guess = input("你的判断 > ").strip().lower()
            except EOFError: guess = "q"
            if guess in ("q","/exit"): print(f"答对 {score}/{answered} 道已答题。"); return
            guess = names.get(guess,guess)
            if guess in GLOSS: break
            print("请输入 1、2、3 或 q。")
        answered += 1; score += guess == gold
        print(f"{'答对' if guess==gold else '再看一眼'}。作者标注：{GLOSS[gold]}；程序判断：{GLOSS[a.audit(text).speech_act]}。")
    print(f"答对 {score}/{answered} 道已答题。")

def repl(a):
    print("PyJev  ·  本地文本审计控制台\n输入待分析文本。不执行、不保存对话、不发通知。\n" + HELP)
    count = 0
    while True:
        try: s = input("pyjev > ")
        except EOFError: print(); return
        cmd = s.strip()
        if cmd in ("/quit","/exit"): return
        if cmd in ("/help","/?"): print(HELP); continue
        if cmd == "/demo": demo(a); continue
        if cmd == "/quiz": quiz(a,rounds=1); continue
        if cmd == "/reset": count=0; print("计数归零；本工具没有对话历史。"); continue
        if not cmd: continue
        count += 1; print(f"#{count}"); one(a,s)

def parser():
    p = argparse.ArgumentParser(prog="pyjev", description="离线判断文本信号与指令意图；不会阻断请求、执行命令或发信。")
    p.add_argument("--version", action="version", version="PyJev "+__version__)
    p.add_argument("-p","--prompt", metavar="TEXT", help="查一句话后退出")
    p.add_argument("-i","--interactive",action="store_true",help="进入交互模式，可与 -p 合用")
    p.add_argument("--json",action="store_true",help="输出 JSON")
    sub=p.add_subparsers(dest="cmd",metavar="COMMAND")
    s=sub.add_parser("scan",help="查单条文本；- 或无参数时读取多行 stdin");s.add_argument("text",nargs="?")
    b=sub.add_parser("batch",help='逐行读取 {"text":"…"}；默认 stdin');b.add_argument("path",nargs="?",default="-")
    sub.add_parser("demo",help="查看讨论、行动与不确定的对照样例")
    q=sub.add_parser("quiz",help="在有标注的例句上进行意图自测");q.add_argument("--rounds",type=int,choices=range(1,10),default=3)
    q.add_argument("--seed",type=int,default=7)
    bench=sub.add_parser("bench",help="复算 320 条公开办公文本的意图分类与分流结果")
    m=sub.add_parser("metrics",help="读取冻结的外部与历史数据集评测结果")
    cmp=sub.add_parser("compare",help="读取与未改动原版 PyBot 的实测结果")
    doc=sub.add_parser("doctor",help="检查随包模型及摘要")
    for child in (s,b,bench,m,doc,cmp):
        child.add_argument("--json",action="store_true",default=argparse.SUPPRESS,help="输出 JSON")
    return p

def dispatch(argv=None):
    p = parser(); args = p.parse_args(argv)
    if args.cmd and (args.prompt is not None or args.interactive): p.error("子命令不能与 -p/-i 混用")
    if args.interactive and args.json: p.error("交互模式不用 --json")
    if args.cmd in ("quiz","demo") and args.json: p.error("演示和游戏只输出人类可读文字")
    a = Auditor()
    if args.cmd == "demo": demo(a); return 0
    if args.cmd == "quiz": quiz(a,args.seed,args.rounds); return 0
    if args.cmd == "doctor":
        for name in ("results.json","pybot-comparison.json","pybot-raw-control.json"): _read(name)
        v={"version":__version__,"model_checksums":"ok","results_checksum":"ok","network_required":False}
        if args.json: emit(v)
        else: print("PyJev "+__version__+"｜模型参数与评测证据校验通过｜离线推断")
        return 0
    if args.cmd == "compare":
        from .comparison import compact
        data=compact()
        if args.json: emit(data)
        else:
            print("固定提交的原版 PyBot 对照（已测汇总；不是现场重跑）")
            for row in data["rows"]:
                acc=row["accuracy_conditional_on_valid"]
                scored="N/A" if acc is None else f"{acc:.1%}"
                print(f"{row['suite']:8s} {row['system']:11s} 合规 {row['valid']}/{row['n']}；正确完成 {row['correct']}/{row['n']}；合规项准确率 {scored}")
            print("没有合规标签时，不可估计条件误报率或召回率。")
        return 0
    if args.cmd == "metrics":
        r=_read("results.json"); n=r["new_external"]["no_overlap"]
        z=r["old_chinese"]["protected_481"]; c=r["new_paired"]["all_normal_discussion"]
        v={"source":"frozen_aggregate_not_a_rerun","controlled_discussion_fp":[c["raw"]["fp"],c["review"]["fp"]],
           "external":{"normal":n["raw"]["tn"]+n["raw"]["fp"],"fp_before":n["raw"]["fp"],"fp_after":n["review"]["fp"],
           "injections":n["raw"]["tp"]+n["raw"]["fn"],"detected":n["review"]["tp"],"missed":n["review"]["fn"]},
           "previously_recovered_still_reviewed":z["still_for_review"],"release_gate_pass":r["all_gates_pass"]}
        if args.json: emit(v)
        else: print(f"冻结成绩（不是现场测试）｜自编讨论误报 {v['controlled_discussion_fp'][0]} → {v['controlled_discussion_fp'][1]} / 120\n"
                    f"外部正常误报 {n['raw']['fp']} → {n['review']['fp']} / {v['external']['normal']}；注入检出 {n['review']['tp']} / {v['external']['injections']}，漏 {n['review']['fn']}。\n"
                    f"历史中文数据集新增检出的 {z['count']} 条仍在复核：{z['still_for_review']}。实验分流未通过全部预设指标。")
        return 0
    if args.cmd == "bench":
        v=replay_office()
        if args.json: emit(v)
        else: print(f"现场复算：{v['texts']} 条；两类文本均判对的配对为 {v['pairs_both_correct']}/{v['pairs']}。\n"
                    f"讨论误进复核：{v['discussion_false_reviews']['baseline']} → {v['discussion_false_reviews']['experimental']} / 120。\n"
                    f"与冻结成绩一致：{v['matches_frozen_evidence']}。")
        return 0 if v["matches_frozen_evidence"] else 1
    if args.cmd == "batch":
        if args.path == "-": return batch(a,sys.stdin.buffer,True)
        with Path(args.path).open("rb") as stream: return batch(a,stream,True)
    if args.cmd == "scan":
        t=args.text
        if t in (None,"-"):
            b=sys.stdin.buffer.read(MAX_WIRE+1)
            if len(b)>MAX_WIRE: print("输入超过字节上限",file=sys.stderr); return 2
            try: t=b.decode("utf-8")
            except UnicodeDecodeError: print("需要 UTF-8 文本",file=sys.stderr); return 2
        one(a,t,args.json);return 0
    if args.prompt is not None: one(a,args.prompt,args.json)
    if args.interactive or (args.prompt is None and sys.stdin.isatty() and not args.json): repl(a)
    elif args.prompt is None: return batch(a, sys.stdin.buffer,False)
    return 0

def main(argv=None):
    try: return dispatch(argv)
    except ModelIntegrityError:
        print("随包模型或证据损坏/缺失，未生成可信结论。请从项目仓库重新安装。",file=sys.stderr);return 1
    except BrokenPipeError: return 0
    except OSError:
        print("无法读取输入或输出。请检查文件路径与权限。",file=sys.stderr);return 2
    except KeyboardInterrupt: return 130
