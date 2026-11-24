"""Generate the public baseline report from verified counts; use --check to detect drift."""
import argparse
import hashlib
from pathlib import Path
from pyjev.api import _read
from pyjev.comparison import measured,SETTINGS,SUITES
here=Path(__file__).resolve().parent
NAMES={"office":"受控办公意图","external":"外部翻译场景","legacy":"历史中文文档"}
SYSTEM={"pyjev":"PyJev · 原生接口","pybot_task":"原版 PyBot · 分类提示","pybot_raw":"原版 PyBot · 原文输入"}

def ratio(x,n):return f"{x:,}/{n:,} ({100*x/n:.1f}%)" if n else "N/A（0 条可评分）"
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def render():
    d=measured();a=_read("pybot-comparison.json");b=_read("pybot-raw-control.json")
    for obj,protocol,adapter in ((a,"PYBOT_PROTOCOL.md","compare_pybot.py"),(b,"PYBOT_RAW_CONTROL.md","raw_control.py")):
        if obj["protocol_sha256"]!=digest(here/protocol) or obj["adapter_sha256"]!=digest(here/adapter):raise ValueError("scoring protocol drift")
    native=d["pyjev"];directed=d["pybot_task"];raw=d["pybot_raw"]
    n=sum(x["n"] for x in directed.values());nraw=sum(x["n"] for x in raw.values())
    v=sum(x["valid"] for x in directed.values());vraw=sum(x["valid"] for x in raw.values())
    errs=sum(x["error"]+x["timeout"] for data in (directed,raw) for x in data.values())
    legacy_cm=native["legacy"]["confusion"]
    legacy_pos=sum(legacy_cm["injected"].values());legacy_neg=sum(legacy_cm["benign"].values())
    lines=["# 原版 PyBot 对照实验", "",
      "## 研究问题与观察", "",
      "检验通用对话接口能否直接用于结构化事后审计。对照为[固定提交的 Hugging Face PyBot](https://github.com/huggingface/pybot/tree/"+a["pybot_commit"]+")，没有改源码、训练分类器或人工重判其自由文本。PyJev 读取自己的显式字段。这里比较的是**任务接口的输出能力**，不是回答质量、安全知识水平或模型真实性。","",
      f"原版 PyBot 在固定分类提示下返回合规标签 **{v:,}/{n:,}**；两个新增评测集不加任务提示、逐字输入原文时为 **{vraw:,}/{nraw:,}**。两个设置共 {n+nraw:,} 次离线单轮调用，均重置状态，可见超时或运行失败合计 {errs} 次。两种设置复用了 {nraw:,} 条文本，不视为额外的独立样本；不同任务不合并计算安全准确率。","",
      "![不同接口的标签覆盖率与正确完成率；下表提供等价文本。](figures/baselines.svg)","",
      "## 端到端任务结果","",
      "| 数据集 | 接口 | 合法标签 / 全部文本 | 正确标签 / 全部文本 | 准确率（仅合法标签） | 非标签 / 超时 / 异常 |",
      "|---|---|---:|---:|---:|---:|"]
    for s in SUITES:
        for k in SETTINGS:
            r=d[k].get(s)
            if r is None:
                lines.append(f"| {NAMES[s]} | {SYSTEM[k]} | 未测 | 未测 | — | — |");continue
            lines.append(f"| {NAMES[s]} | {SYSTEM[k]} | {ratio(r['valid'],r['n'])} | {ratio(r['correct'],r['n'])} | {ratio(r['correct'],r['valid'])} | {r['no_label']} / {r['timeout']} / {r['error']} |")
    lines+=["","**读法：**结构不合规降低“完成率”，不是一条被证明在语义上错误的回答。§unclear§ 是可评分的意图类；没有标签不是 §unclear§。同一批文本适配了不同接口，不能把此表解释为泛化语言理解能力的排名。","","## 注入二分类的条件指标","",
        "![注入检出与正常文本误报：原版 PyBot、双语词项规则与 PyJev 在相同文本上的分项对照；无可评分输出单列。](figures/detection.svg)","",
        "| 数据集 | 接口 | 误报 / 可评分正常项 | 检出 / 可评分注入项 |","|---|---|---:|---:|"]
    for s in ("external","legacy"):
        for k in SETTINGS:
            r=d[k].get(s)
            if not r:continue
            lines.append(f"| {NAMES[s]} | {SYSTEM[k]} | {ratio(r['false_positives'],r['valid_normals'])} | {ratio(r['true_positives'],r['valid_positives'])} |")
    lines+=["","上述分母为空时不是 0% 误报或 0% 召回。PyJev 的二分类列使用保守的 §review§；讨论分流是另一项消融，见[研究主页](../README.md)。","",
        f"**类别比例的影响。** 历史中文数据集的注入比例是 {ratio(legacy_pos,legacy_pos+legacy_neg)}。即使将所有文本一律送入复核，总体正确率也能达到这一数值，但正常文本将有 {legacy_neg}/{legacy_neg} 被误报。因此不以跨数据集汇总准确率宣称安全性能提升。","","## 实验控制","",
        "- **任务设置**：320 条语用意图文本（120 讨论、120 行动、80 不确定），353 条外部翻译样本（153 注入、200 正常），1,384 条历史中文文档（1,323 注入、61 正常）。两种系统使用同一批文本、相同的参考标注；不根据输出筛选样本。原文设置仅预注册在这两个新增评测集上。","- **输入差异**：分类提示条件以固定中英双语任务描述包裹原文；同文条件把原文逐字交给原版。PyJev 两者均直接审计原文。PyBot 返回一个原始回复，使用预注册的整段短标签解析器；不从长文本、拒答或转述中猜标签。","- **隔离**：核对原版 528 个 Python 文件与官方单次 §-p§ 的中性样例输出。每个样本使用独立子进程和空记忆，固定种子 20261124 与哈希种子 0。只读取固定资料；无网络、无生产挂载、无外部模型，无原文/自由回复导出。每条原版调用上限 30 秒，无重试。",
        f"- **环境**：Linux 容器，Python {a['python']} / {a['machine']}。场景为功能比较，不能引用为吞吐、延迟或生产容量测试。",
        "- **评分前固定**：主协议与评分程序见[提交 8f04bd0](https://github.com/123yjf/pyjev_ai_security/commit/8f04bd0cdff65a28e83ddf99535a4d5f1ac12143)，同文对照见[提交 ff664ee](https://github.com/123yjf/pyjev_ai_security/commit/ff664ee7776935f3b1861b98d37d3a35db80e9fc)。两项均先固定于本地 Git，再计分；不是第三方注册。公开数据按固定摘要验证。使用既有评测集比较接口，不是 PyJev 的独立新盲测。","",
        "## 复现与原始计数","",
        "- [主实验逐类混淆计数](../pyjev/data/pybot-comparison.json) · [同文对照计数](../pyjev/data/pybot-raw-control.json) · [评分器](../research/compare_pybot.py)。",
        "- 安装包中 §pyjev compare§ **读取**已测结果。要重跑原版，使用[隔离复现步骤](../research/BASELINE_REPLAY.md)；仅查看或复算 PyJev 意图题无需 Docker。",""]
    return "\n".join(lines).replace("§",chr(96))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--check",action="store_true");a=p.parse_args();out=render()
    if a.check:
        if out!=(here.parent/"docs/comparison.md").read_text():raise SystemExit("comparison report is stale")
    else:print(out,end="")
if __name__=="__main__":main()
