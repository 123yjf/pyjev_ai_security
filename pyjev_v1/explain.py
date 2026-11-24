"""Chinese rendering of the native routing decision; no new classification."""
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

def explain_en(data):
    """Describe what was observed without inferring authorization or execution."""
    if data["execution_evidence"] != "not_observed" or data["service_action"] != "none":
        raise ValueError("Unrecognized execution contract.")
    intent = {"mention": "Discussing or quoting an instruction.",
              "act": "Asking the assistant to act; this alone is not an attack.",
              "unclear": "Intent could not be determined."}[data["speech_act"]]
    signal = {"suspected": "Possible prompt injection; not proof of an attack.",
              "no_signal": "No injection signal found; not proof of safety.",
              "unknown": "The input could not be assessed."}[data["signal"]]
    route = {"review": "Send this text for human review.",
             "case_review": "Review the reported event, not the person reporting it.",
             "record_only": "Mark the context in the result only; do not queue a review.",
             "no_signal": "No review suggested.",
             "incomplete": "No audit decision; do not count this as a pass."}[data["route"]]
    return "\n".join(("Intent: " + intent, "Signal: " + signal, "Review: " + route,
                     "Action: Nothing was executed, blocked, stored or sent. External execution was not observed."))
