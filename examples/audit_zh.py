"""Human-readable, source-checkout-only view of the original audit. No text is saved or echoed."""
import argparse
import json
import sys

from pyjev import Auditor
from pyjev.api import ModelIntegrityError
from pyjev._detector import LIMIT

INTENT = {"mention": "文字在讨论或引用指令。", "act": "文字要求助手实际办理；这本身不是攻击。",
          "unclear": "仅凭这段话，无法确定是否在要求助手办理。"}
SIGNAL = {"suspected": "发现提示注入线索；不是攻击定论。", "no_signal": "未检出提示注入线索；这不是安全证明。",
          "unknown": "本次无法判断是否有提示注入线索。"}
ROUTE = {"review": "建议人工复核这段文字。", "case_review": "建议人工复核被叙述的事件，不是认定当前用户在发指令。",
         "record_only": "只在本次返回值里标记语境，不建议送审，也没有写入日志。", "no_signal": "本次不建议送审。",
         "incomplete": "未完成审计，不能当作正常或安全。"}

def explain(data):
    """Translate the effective route, never the baseline or shadow route in its place."""
    route = data["route"] if "route" in data else data["review"]
    if data["execution_evidence"] != "not_observed" or data["service_action"] != "none":
        raise ValueError("未知执行契约，拒绝猜测。")
    intent = INTENT[data["speech_act"]] if route != "incomplete" else "输入不可分析，本次不解释意图。"
    return "\n".join(("文字意图：" + intent, "注入线索：" + SIGNAL[data["signal"]], "复核建议：" + ROUTE[route],
                      "实际动作：本程序没有执行或拦截，也没有发信；看不到其他系统是否执行。"))

def main(argv=None):
    p=argparse.ArgumentParser(description="从标准输入读取一段 UTF-8 文本，不回显正文。默认读 v0.1.0。")
    p.add_argument("--scope",action="store_true",help="显式选择 Scope-1 研究候选")
    p.add_argument("--json",action="store_true",help="不翻译；输出该版本原生 JSON，字段不增删")
    args=p.parse_args(argv)
    try:
        buf=sys.stdin.buffer.read(4*LIMIT+1)
        text=buf.decode("utf8","strict") if len(buf)<=4*LIMIT else None
    except UnicodeDecodeError:
        text=None
    try:
        if args.scope:
            from candidates.scope1 import ScopeAuditor
            result=ScopeAuditor().audit(text).as_dict()
        else:
            result=Auditor().audit(text).as_dict()
    except ModelIntegrityError:
        print("模型完整性校验失败；没有审计结论。",file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True) if args.json else explain(result))
    return 2 if result.get("route",result.get("review"))=="incomplete" else 0

if __name__=="__main__":
    raise SystemExit(main())
