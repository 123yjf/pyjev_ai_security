"""Local discourse/ownership predicates; are we discussing, acting or describing a case?"""
from dataclasses import dataclass
import re

def rx(s):return re.compile(s,re.I)
# Public linguistic categories, not source names, IDs, test data or per-document exceptions.
META=rx(r"提示(?:词|语|工程|设计|模板|注入)|\bprompt(?:s|ing)?\b|系统(?:设定|指令|提示)|初始(?:设定|指令)|角色(?:设定|指令)|人设|persona|设定.{0,6}(?:助手|角色)|给.{0,16}(?:机器人|助手|工具).{0,8}(?:规则|设定)|(?:机器人|助手).{0,8}(?:规则|话术)")
EDIT=rx(r"解释|解读|意思|含义|说明|示[例范]|举例|称为|指的是|是指|教程|讲解|讨论|描述|探讨|定义|表述|措辞|写法|教.{0,4}设计|写得|设定.{0,5}合适|怎[么样].{0,6}(?:写|表述|描述|改)|建议|评[价议]|你觉得|请教|自然吗|帮我改|改得|细化|优化.{0,12}(?:提示|设定|文字)|如何.{0,8}(?:设计|配置|撰写|设置|理解|编写)")
DOC=rx(r"指南|培训|教学|公告|通告|技术文档|配置(?:文件|范例|示例|模板)|供.{0,8}参考|教程|示例(?:配置|指令|提示)|用作示例|不是.{0,8}(?:实际|当前).{0,8}指令|仅用于|本章节|本节|下面的?例子|以下.{0,10}(?:示例|配置|例子)")
PROTECT=rx(r"防范|防止|警惕|识别|防护|避免|防御|防御措?施|建议|缓解|防御策略|风险|不应|不应该|不要执行|拒绝|不得执行")
RISK_TOPIC=rx(r"提示(?:词)?注入|prompt injection|间接注入|指令(?:注入|劫持)|越权指令|越狱")
SPEAKER=rx(r"用户|客户|员工|同事|你|我|助手|机器人|模型|智能体|代理|agent|文档|邮件|网页|工具")
ACTOR=rx(r"助手|机器人|模型|智能体|代理|\bagent\b|\bai\b|助理|copilot")
CARRIER=rx(r"邮件|来信|网页|网站|页面|文档|知识库|附件|工具(?:调用|结果|返回|输出)|搜索结果|检索|回复|返回(?:值|结果|内容)|响应|提[交取]记录|工单|表格|表单|日志|页面|文件|评论|备[忘注]|通知|日历|聊天记录|消息|字段|正文|插件|仓库|简历|合同|会议|数据源|链接")
EMBED=rx(r"夹带|夹杂|混入|植入|嵌入|藏有|隐藏|暗藏|插入|注入|写着|写道|写有|包含|出现|声称|宣称|自称|伪[装称造]|冒充|附带|附有|附加|要求|指示|诱导|劫持|让.{0,8}(?:助手|智能体|代理|模型)|请求.{0,4}(?:助手|代理)")
REPORTED=rx(r"攻击者|第三方|外部|被.{0,8}(?:诱导|劫持|操控|指示)|收到|读[到取]|收取|获取|抓取|返回|检索|发现|弹出|展示|显示|加载|解析|响[应答]|处理|打开|中.{0,5}(?:隐藏|出现|要求|包含|写着)|提示注入|间接注入|劫持")
DIRECTIVE=rx(r"指令|命令|指示|要求|让.{0,5}(?:它|助手|模型)|请.{0,8}(?:调用|执行|发送)|系统消息|系统提示|优先级|授权|确认|\binstructions?\b")
SENSITIVE=rx(r"未经授权|未授权|越权|绕过|规避.{0,5}(?:审批|授权|检查)|忽[略视].{0,12}(?:规则|授权|指令|要求|之前|用户)|跳过.{0,6}(?:审批|验证|确认)|凭[据证]|密[钥码]|口令|令牌|隐私|机密|敏感|泄[漏露]|外[传发]|窃取|上传|转[账帐发]|删除|执行.{0,5}(?:命令|脚本)|解锁|开锁|开门|支付|汇款|扫码|退款|转给|代发|授权码|验证码|权限|认证|静默|外部地址|数据.{0,4}披露|账户|银行|信用卡|收款|银行[卡账]|\bpassword\b|credential")
CHANGE=rx(r"更改|改[为成]|修改|切换|设置|提交|发送|投递|复制|转交|粘贴|分享|打印|输出|联系|安装|运行|转移|调用|访问|添加|打开|创建|下单|预订|拉黑|关注|公开|发布|邀请|下载|确认|执行|重置")
ASK=rx(r"请(?!勿|注意|见|参考)|帮我|替我|能否|能不能|麻烦|给我|帮忙|我想(?:要|让你)|我需要|为我|务必|你(?:必须|现在要|需要|来|负责)|立刻|立即|照做|照办|按.{0,10}(?:执行|办理|操作)|^把|请问|我[要想].{0,6}(?:查询|预订|知道|了解)")
TASK=rx(r"查[找看询]|搜[索寻]|整理|归档|归类|列[出表]|编号|转交|保存|安排|预[订约]|计算|翻译|总结|检索|推荐|比较|创建|制定|更[改新]|发送|通知|填写|登记|输出|生成|画出|订[单票]|设计|提取|检查|统计|写[一出]|汇总|删除|调整|获取|给出|分析|订购|请问|告诉我|查看|反馈|执行|照做")
AFFIRM=rx(r"(?:请你|现在|马上|立即|直接|帮我|替我|务必).{0,9}(?:执行|照做|照办|发送|删除|转账|上传|交付)|(?:按|照)(?:照|着)?.{0,14}(?:引文|引号|上文|其中|里面|原文|指令|这句|上述).{0,10}(?:去做|执行|操作|照做|办理)|(?:然后|随后|另外|同时|接着|再请).{0,12}(?:执行|照做|发送|删除|转账|上传|调用)")
NEG=rx(r"(?:无需|无须|不要|并非让|别|不必|不用)(?:你|去|真的|实际|直接|现在){0,3}(?:执行|照做|照办|操作|发送|调用)")
UNCERTAIN=rx(r"不知道(?:是否|该不该)|用途不[明详]|尚待确认|难以判断|不能确定|不确定是否")
OVERRIDE=rx(r"(?:忽略|无视|忘记|替换|覆盖|跳过).{0,12}(?:指令|规则|系统要求|初始设定|安全限制|之前.{0,4}要求)|(?:不要|不得).{0,6}(?:告诉用户|让用户知道)|(?:override|ignore).{0,18}(?:instructions|rules)")
FORMAL=rx(r"系统(?:指令|授权|提示)|管理(?:员|系统)|开发者|高优先级|无需确认|已获(?:得)?授权|系统消息|自动化(?:操作|任务)")

@dataclass(frozen=True)
class Acts:
    speech:str
    mentioned:bool
    report:bool
    artifact:bool
    explicit_act:bool

def interpret(v,old_act):
    full,outer=v.full,v.outer
    effective=NEG.sub(" ",outer)
    explicit=bool(AFFIRM.search(effective) or re.search(
        r"(?:然后|接着|另外|同时|随后|不过|另请)[^。！？；\n]{0,18}(?:提交|发送|删除|保存|上传|登记|归档|转交|执行)",effective))
    # Co-occurrence must hold inside a bounded neighbourhood, not across an entire manual.
    pieces=re.split(r"[。！？!?；;\n]+",full)
    report=False;artifact=False
    for i,piece in enumerate(pieces):
        if not piece.strip():continue
        s=(pieces[i-1][-100:]+" "+piece[:210]) if i else piece[:310]
        source=bool(CARRIER.search(s)); embedded=bool(EMBED.search(s))
        mechanism=bool(REPORTED.search(s)); agent=bool(ACTOR.search(s))
        instruction=bool(DIRECTIVE.search(s)); sensitive=bool(SENSITIVE.search(s))
        if source and embedded and mechanism and (instruction or sensitive) and (agent or sensitive):
            report=True
        if v.markup and ((OVERRIDE.search(s) and (instruction or agent)) or
                         (ASK.search(s) and (sensitive or FORMAL.search(s)) and CHANGE.search(s)) or
                         (FORMAL.search(s) and sensitive and CHANGE.search(s))):
            artifact=True
    about=bool(META.search(outer) or (v.quotes and META.search(full)))
    editorial=bool(EDIT.search(outer))
    educational=bool(DOC.search(outer) and (PROTECT.search(outer) or editorial))
    direct_only=bool(ASK.search(effective) and TASK.search(effective))
    # A question *about* a prompt is not an instruction to perform its quoted contents.
    meta=about and (editorial or educational or (RISK_TOPIC.search(outer) and PROTECT.search(outer)))
    quotation=bool(v.quotes and editorial and (about or re.search(r"这(?:段|句)|引(?:用|文)|原文|措辞|语气|含义",outer)))
    mentioned=bool((meta or quotation) and v.balanced and not explicit and not v.markup)
    if explicit: speech="act"
    elif mentioned: speech="mention"
    elif report: speech="unclear"
    elif UNCERTAIN.search(outer):speech="unclear"
    elif direct_only:speech="act"
    else:speech=old_act
    return Acts(speech,mentioned,report,artifact,explicit)
