"""Harmless, fixed office examples for interactive use. No external models or data."""
from ._office import TOPICS, PAIRS, UNCLEAR

GLOSS = {"mention":"在谈论或引用", "act":"要求落实这件事", "unclear":"无法从文字确定"}
SIGNALS = {"suspected":"发现可疑文本信号", "no_signal":"没有命中，不等于安全", "unknown":"材料不完整"}
ROUTES = {"review":"保留复核", "record_only":"仅留记录", "no_signal":"无原始信号", "incomplete":"信息不足"}

def triplet(topic: int = 0, pair: int = 0) -> list[tuple[str, str]]:
    q = "“" + TOPICS[topic] + "”"
    a, b = PAIRS[pair]
    return [(a.format(q=q), "mention"), (b.format(q=q), "act"), (UNCLEAR[0].format(q=q), "unclear")]

def describe(r) -> str:
    return (f"原始信号：{r.signal}（{SIGNALS[r.signal]}）｜意图：{r.speech_act}（{GLOSS[r.speech_act]}）\n"
            f"默认复核：{r.review}（{ROUTES[r.review]}）｜实验建议：{r.experimental_review}"
            f"（{ROUTES[r.experimental_review]}）｜执行证据：未观测，不授权。")
