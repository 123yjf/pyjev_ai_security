# 方法、数据与可复现性

## 研究问题

任务 A 是单段文本的提示注入信号检测，正类是发布者标为注入的文本。任务 B 是中文语用意图分类：区分讨论/引用指令、要求助手落实指令、文本不足以定夺。**任务 B 不是任务 A 的替代标签**：一次正常的排版请求可以是行动请求；一封来信出现可疑内容，不代表转发来信的人要求执行。

原始信号与实验分流分别记录。“误报”在本文专指**发布者/作者标为正常的文本被送入复核**；“漏检”指正类没有进入复核。未检测到信号不是“安全”的判定。我们不研究模型身份或恶意工具的实际执行，也没有使用生产流量。

## 模型与训练

1. **信号层（checkpoint 323）**：保留原词项基线和双语词项基线的命中，额外使用带 L2 正则和类别平衡的线性文本判别器。学习对象为哈希化词项/字符片段；完整模型含 16,000 个加权特征。原文训练块共 546 条，另取标签逐行对齐的 546 条多语文本，不应解释为 1,092 个独立问题。近重复原题和译本按家族分在同一折；用折外验证在 1,000 次更新中选定第 323 轮。`pyjev/data/rulebook.json` 是冻结参数，不是训练语料。
2. **意图层**：三分类、字符片段与外层语句结构、L2 正则化；对成对引用中的内容做边界处理。225 道自编、无害办公题分为 5 组、75 个表达家族。每折留一组，每次拟合 1,000 步。阈值只在训练的折外预测上选：先要求没有明确行动/待定被折外错判为讨论，再选正确讨论最多者；同分取较高阈值。选定 0.90，**并非经校准的 90% 概率**。材料复杂或说话者难以判断时保留复核。
3. **不自动分流**：只有实验字段允许把原始阳性且明确仅为讨论的文本标为 `record_only`。所有审计记录仍保留原始信号，默认字段从不因此撤销复核。现场执行、授权、收费与此无关。

## 数据与证据

独立的[中文企业场景专用检测器盲评](enterprise/README.md)在 v0.1.0 固定后进行；与下表训练或既往复盘分开。[正文、图表和证据边界](../docs/enterprise-blind.md)。

| 来源 | 用途 | 固定版本或校验 |
|---|---|---|
| [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections/tree/4f61ecb038e9c3fb77e21034b22511b523772cdd) | 原始信号层训练块 | 版本 `4f61ecb`；数据卡 Apache-2.0 |
| [rikka-snow/prompt-injection-multilingual](https://huggingface.co/datasets/rikka-snow/prompt-injection-multilingual/tree/f1ad1f3dd44581f53a4c67e96a9dde2fb419ee5b) | 双语训练块 | 版本 `f1ad1f3`；数据卡 MIT |
| [225 条训练配方](curriculum.py) / [320 条受控测试配方](../pyjev/_office.py) | 意图模块训练 / 已公开保留集 | 5 折按表达家族分组，无客户对话；测试用 12 对句式 × 10 个主题及 80 条未指明任务 |
| [外部翻译场景数据及来源说明](https://huggingface.co/datasets/WhitzardAgent/AgentSafety-All-in-One-Test-Case/blob/080e55c78f27bb1576c4138b053cdd405bc3198f/prompt-injection/trans-prompt-injection/README.md) | 专项外部二分类，353 条 | 来源说明注明 [Sirius1906](https://github.com/Sirius1906/trans-prompt-injection-detector)；固定修订 `080e55c`；语种为数据集标注，包含混合语言 |
| [JiachengWu591/zh-ipi-bench](https://huggingface.co/datasets/JiachengWu591/zh-ipi-bench/tree/29f870e3181a329251d9145cda0b60513dc188a0) | 历史中文文档回归 | v3，文件含 1,556 条，取中文 1,384 条；不冒充新盲测 |
| 原项目 48 条正常业务文本 | 既有误报回归 | 仅发布冻结汇总；不在 `pyjev bench` 的 320 条分母内 |
| [原版 Hugging Face PyBot](https://github.com/huggingface/pybot/tree/7d63c7fbebb44c7e466e5c8b5c1f341ab767929e) | 未改动的通用对话接口基线 | 版本 `7d63c7f`；[预注册方法](PYBOT_PROTOCOL.md)、[无额外提示对照](PYBOT_RAW_CONTROL.md)、[数表](../docs/comparison.md) |

公开的是原项目自行实现的推断代码、冻结权重、无害办公样例、聚合计数；没有复制第三方语料或 PyBot 自身代码。研究协议使用固定 token 五元组 Jaccard ≥ 0.70 筛近重复，353 条新外部题无命中，不能据此排除语义近似。原始/保留复核集合使用固定排序的题目标识摘要逐行对齐。完整结果：[冻结证据 JSON](../pyjev/data/results.json)，[训练折外校准](calibration.json)。

## 完全离线可复算

### 同任务检测器的补充对照

原版 PyBot 是通用聊天接口，不是下表的“基线规则”。为独立衡量检测能力，另在相同二分类数据上重放 PyJev 的冻结组件。每格为 **真阳性 / 全部注入；误报 / 全部正常**。不重新拟合或选择参数。

| 信号系统 | 外部翻译场景 | 历史中文文档 |
|---|---:|---:|
| 原文训练的词项规则 | 28/153；0/200 | 345/1,323；2/61 |
| 同法、双语训练的词项规则 | 28/153；0/200 | 345/1,323；2/61 |
| 规则加线性分类器（第 323 轮） | 61/153；0/200 | 826/1,323；5/61 |
| 再加意图分流（实验） | 61/153；0/200 | 826/1,323；5/61 |

[原版 PyBot、双语词项规则与 PyJev 的召回率及误报率对照图](../docs/figures/detection.svg)同时显示分子、分母及不可估计项，不把无标签回复算作正常。

在历史中文数据集上，加入线性分类器后多检出 481 条，同时多 3 条误报。最后一行在这两组上均没有进一步减少误报；自编讨论组的变化不能替代此结果。[完整混淆计数](signal-controls.json)；用 `python -m research.signal_controls --external /path/to/translation-cases.jsonl --legacy /path/to/zh-ipi-v3.jsonl` 可离线重算。

### 运行与复现

从项目根目录运行：

~~~bash
python -m pyjev doctor
python -m pyjev bench --json          # 现场复算自编题，含混淆矩阵
python -m unittest discover -s tests -v
~~~

如已准备公开的原始数据文件：

~~~bash
python -m research.replay external /path/to/translation-cases.jsonl
python -m research.replay legacy /path/to/zh-ipi-v3.jsonl
~~~

[外部数据文件](https://huggingface.co/datasets/WhitzardAgent/AgentSafety-All-in-One-Test-Case/resolve/080e55c78f27bb1576c4138b053cdd405bc3198f/prompt-injection/trans-prompt-injection/cases.jsonl) 和 [历史中文 v3 文件](https://huggingface.co/datasets/JiachengWu591/zh-ipi-bench/resolve/29f870e3181a329251d9145cda0b60513dc188a0/data/v3.jsonl) 都按[精确 SHA-256](replay.py)校验。也支持 `-` 从管道读取。只当作惰性文本，从不执行来源仓库的生成器或样本文字。程序不主动联网，不回显自由文本。未通过校验不出分。

开发者可选安装研究依赖，重训**意图层**或重画图（推断不需要这一步）：

~~~bash
python -m pip install -e ".[research]"
python -m research.fit_intent                  # 报参数摘要，不覆盖模型
python -m research.fit_intent --out /tmp/my-intent-head.json
python -m research.figures --out docs/figures  # 中文需 CJK 字体；可用 --lang en
python -m research.figures --format pdf --out /tmp/pyjev-paper-figures  # 论文矢量图；也可选择 300-dpi PNG
~~~

中文 PDF 选择带 TrueType 轮廓的中文字体，使文字可复制；可用 `--font "字体名称"` 指定本机已装字体。SVG 将文字转为矢量路径，不依赖读者安装相同字体。

NumPy/BLAS 的不同实现可能使浮点权重字节略有不同。重训输出路径必须是新文件。此仓库提供信号层的冻结推断和复算，不宣称提供其从零训练流水线。图表报告原始计数与分母。已用于回归测试的样本不作为新盲测；这些描述性结果不能外推为生产环境误报率、召回率或安全承诺。
