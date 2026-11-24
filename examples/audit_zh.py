"""Human-readable, source-checkout-only view of the original audit. No text is saved or echoed."""
import argparse
import json
import sys

from pyjev import Auditor
from pyjev.api import ModelIntegrityError
from pyjev._detector import LIMIT

from pyjev_v1.explain import explain

def main(argv=None):
    p=argparse.ArgumentParser(description="从标准输入读取一段 UTF-8 文本，不回显正文。默认读 v0.1.0。")
    p.add_argument("--v1", action="store_true", help="使用 pyjev_v1")
    p.add_argument("--scope", dest="v1", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--json",action="store_true",help="不翻译；输出该版本原生 JSON，字段不增删")
    args=p.parse_args(argv)
    try:
        buf=sys.stdin.buffer.read(4*LIMIT+1)
        text=buf.decode("utf8","strict") if len(buf)<=4*LIMIT else None
    except UnicodeDecodeError:
        text=None
    try:
        if args.v1:
            from pyjev_v1 import Auditor as V1Auditor
            result=V1Auditor().audit(text).as_dict()
        else:
            result=Auditor().audit(text).as_dict()
    except ModelIntegrityError:
        print("模型完整性校验失败；没有审计结论。",file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True) if args.json else explain(result))
    return 2 if result.get("route",result.get("review"))=="incomplete" else 0

if __name__=="__main__":
    raise SystemExit(main())
