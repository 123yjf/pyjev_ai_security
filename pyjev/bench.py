"""Replay the 320 harmless published office cases. Other datasets are never silently fetched."""
from collections import defaultdict
from .api import Auditor, _read
from ._intent import LABELS
from ._office import exam

def replay_office() -> dict:
    expected = _read("results.json")["new_paired"]
    a = Auditor(); cm = {g:{p:0 for p in LABELS} for g in LABELS}
    sides = defaultdict(dict); demotions = []; ment_raw = ment_shadow = total_raw = total_shadow = 0
    for text, gold, pair in exam():
        r = a.audit(text); cm[gold][r.speech_act] += 1
        if pair is not None:
            sides[pair][gold] = r.speech_act
        total_raw += r.review == "review"; total_shadow += r.experimental_review == "review"
        if gold == "mention":
            ment_raw += r.review == "review"; ment_shadow += r.experimental_review == "review"
            if r.review == "review" and r.experimental_review == "record_only":
                demotions.append(pair)
    both = sum(v.get("mention") == "mention" and v.get("act") == "act" for v in sides.values())
    verified = (cm == expected["confusion_truth_then_predicted"] and both == expected["pairs_both_correct"]
                and len(sides) == expected["pairs_all"] and
                [ment_raw, ment_shadow] == [expected["all_normal_discussion"][c]["fp"] for c in ("raw","review")]
                and [total_raw, total_shadow] == [expected["all_safe_office_text"][c]["fp"] for c in ("raw","review")])
    return {"suite":"authored_office", "texts":sum(sum(row.values()) for row in cm.values()),
            "pairs":len(sides), "pairs_both_correct":both, "confusion":cm,
            "discussion_false_reviews":{"baseline":ment_raw, "experimental":ment_shadow, "normal_texts":sum(cm["mention"].values())},
            "demoted_discussion_cases":{"n":len(demotions),"distinct_topics":len({k[0] for k in demotions}),"distinct_frames":len({k[1] for k in demotions})},
            "matches_frozen_evidence":verified}
