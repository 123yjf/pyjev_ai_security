"""Relational evidence for incoming artifacts versus reports about someone else's instruction."""
from dataclasses import dataclass
import re

SOURCE=re.compile(r"网页|页面|文档|电子?邮件|附件|页脚|邮件|通知|弹窗|手册|示例|消息|消息体|返回|工具输出|摘要|仓库|工单|工作区|评论|日历|条目|海报|图像|图[片像]|描述|简历|链接|检索|搜索结果|知识库|群聊|门户|表单|第三方|外部|回复|回执|字段|代码注释")
INSERT=re.compile(r"嵌入|暗藏|隐藏|藏在|夹带|插入|混入|植入|附带|篡改|假冒|冒充|伪装|伪造|声称|伪称|诱[骗导]|劫持|夹杂|取代|替换|骗[取过]|误导|被动手脚|欺骗|注入|指示|强[迫制]|要求|写[着道]|敦促|试图.{0,10}让|假借|宣称|里面说")
TARGET=re.compile(r"(?i:agent|llm|(?<![a-z])ai(?![a-z])|copilot)|助手|助理|代理|大模型|语言模型|智能体|聊天机器人|自动化系统")
HOSTILE=re.compile(r"攻击者|恶意|未经授权|未获授权|无关.{0,6}任务|越权|绕过|冒充|伪造|钓鱼|窃取|外泄|外传|泄露|欺骗|篡改|劫持|诱导|偷偷|暗中|静默|伪装|提示(?:词)?注入|间接注入")
CLAIM=re.compile(r"系统(?:消息|指令|要求|提示|通知)|管理员|假冒|冒充|伪造|无需.{0,6}确认|已授权|高(?:于|优先级)|必须|强行|强制")
DESC=re.compile(r"攻击者|有人|收到|打开|取回|读取|浏览|访问|显示|结果|写[着道]|声称|要求|呈现|出现在|中.{0,6}(?:有|嵌入|包含)|导致|从而|诱导|试图|被.{0,8}(?:篡改|诱导|劫持)|使.{0,6}(?:模型|助手)")
EFFECT=re.compile(r"指令|指示|命令|用户指示|执行|输出|采取|调用|发送|转[移交发账帐]|退款|支付|下单|删[除掉]|更改|注入|凭据|敏感|机密|隐私|权限|覆盖|授权|评价|忽略|传输|取回|泄露|修改|操作|关闭|开锁|解锁|粘贴|提交|下载|上传|网址|账号|调用函数")
IMPER=re.compile(r"请(?!见|参考|注意)|务必|马上|立[即刻]|必须|帮我|替我|需要你|接下来|继续|现在|不要告诉|无需确认|(?i:\b(?:must|please|call|invoke|execute|mandatory|immediately)\b)")
CAPABILITY=re.compile(r"(?:调用|运行|执行|invoke|call).{0,15}(?:工具|函数|接口|命令|命名|api|tool|function)|\b[a-z][a-z0-9]*_[a-z][a-z0-9_]{2,}(?:\s*\(|\b)")
BREAK=re.compile(r"[。！？!?；;\n]+")
@dataclass(frozen=True)
class Evidence:
    report:bool=False
    artifact:bool=False

def evidence(v):
    parts=[s for s in BREAK.split(v.full) if s.strip()]
    report=False;artifact=False
    for i,q in enumerate(parts):
        # Preserve short-distance provenance; a footnote does not govern an entire long document.
        for j in range(0,len(q),224):
            s=((parts[i-1][-112:]+" ") if i and j==0 else q[max(0,j-72):j])+q[j:j+270]
            carrier=SOURCE.search(s); splice=INSERT.search(s); audience=TARGET.search(s)
            harm=HOSTILE.search(s); outcome=EFFECT.search(s); authority=CLAIM.search(s)
            if carrier and splice and outcome and (audience or harm or authority) and DESC.search(s):
                report=True
            if audience and harm and outcome and re.search(r"导致|诱导|操[纵控]|劫持|被迫|使.{0,10}(?:模型|助手)|欺骗|注入|窃取|篡改",s):
                report=True
            if v.markup and outcome and ((IMPER.search(s) and (CAPABILITY.search(s) or harm or authority)) or
                                        (audience and authority and splice)):
                artifact=True
    return Evidence(bool(report),bool(artifact))
