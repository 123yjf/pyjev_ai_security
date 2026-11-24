# 输入输出契约 · schema v1

在接入方已有的异步审计流程中，把一段**已经获得授权用于审计**的文本交给 `audit(text)`。调用本身是同步的本地纯计算；库没有部署队列，不会替接入方把工作移出请求主链路。意图标签描述文本里**被提及的动作**，不是分析器要做的事情。

## 输入

- Python 3.10+ 的 `str`；不接收 URL、文件指令、账号、模型密钥或会话凭据。可分析长度是 1–32,768 个 Unicode 字符（非纯空白，无孤立 surrogate）。不对超长文本悄悄截断。
- `-p TEXT` 是单条无敏感演示；`scan -` 从 stdin 收整篇，`batch [文件|-]` 严格读取每行一个仅有 `text` 字符串字段的 UTF-8 JSON 对象。普通管道 `... | pyjev` 是**一行一条原始文本**，不是 JSONL 或多行单篇。
- `batch` 每个物理行最多 256 KiB（不含 CRLF）；`scan -` 的整份输入最多 256 KiB。错误记录不会中止后续有效记录。不要把密钥放命令行；操作系统、外部终端和调用方的日志不在本库控制范围内。
- JSONL 重复字段返回 `duplicate_field`，不会悄悄取最后一个值。CLI 批处理输入和样本内容不会被解释为工具调用；交互斜杠命令只在显式终端模式中生效。

## 输出

`audit` 返回不可变的 `Audit`；`as_dict()` 和 `--json` 遵循 [JSON Schema](audit.schema.json)。不返回原文、邮箱、token、审批结果或伪造的置信度。

| 原始信号与外层判断 | `review`（保守） | `experimental_review`（仅供比较） |
|---|---|---|
| `unknown`（输入不可分析），意图 `unclear` | `incomplete` | `incomplete` |
| `no_signal`（任意意图） | `no_signal` | `no_signal` |
| `suspected` 且 `mention` | `review` | `record_only` |
| `suspected` 且 `act` 或 `unclear` | `review` | `review` |

`speech_act=unclear` 是一个有意义的语义标签，不等于输入损坏。正常行动请求可以是 `signal=no_signal, speech_act=act`。相反，别人写的检索文档可能存在 `signal=suspected, speech_act=unclear`：有可疑文字，不代表当前用户在发号施令。

所有结果都包含 `execution_evidence="not_observed"`、`grants_authority=false`、`service_action="none"`、`schema_version=1`。没有后台请求、发信、执行或持久化；**不代表**第三方客户端没有执行。文件缺失或哈希不符时 Python 抛出 `ModelIntegrityError`，不要降级成 `no_signal`。

## 批处理与退出码

`pyjev batch examples/office.jsonl` 的每个输出对象是 `{"line":1,"audit":{...}}`。格式、编码或行字节边界错误时是 `{"line":2,"error":"invalid_json"}` 等，不回显输入。行号从 1 起，错误行也占一个编号。合法格式但文本空白或超过字符数返回 `incomplete`，不伪装成正常。

| 退出码 | 含义 |
|---|---|
| 0 | 完成，包括“可疑文本”以及已按规范输出的 `incomplete`；不是安全背书。 |
| 1 | 证据/模型完整性或冻结验收复算失败。 |
| 2 | 指令、文件、传输编码、字节上限或 JSONL 格式错误（批处理仍输出其他行）。 |
| 130 | 用户中断。 |

健康探活应看 `pyjev doctor`，不要用“有没有告警”判断进程是否健康。请勿直接按 `experimental_review` 自动拦截、封禁或通知客户。
