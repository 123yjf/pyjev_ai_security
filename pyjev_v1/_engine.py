"""Frozen discourse decisions, exposed independently of the default pyjev policy."""
from dataclasses import asdict, dataclass
import re
from pyjev import Auditor as BaselineAuditor
from .discourse import (AFFIRM, ASK, CHANGE, DOC, EDIT, FORMAL, META, NEG, OVERRIDE,
                        PROTECT, RISK_TOPIC, SENSITIVE, TASK, interpret)
from .view import view
from .evidence import evidence

@dataclass(frozen=True)
class Decision:
    original_signal:str
    original_review:str
    signal:str
    speech_act:str
    route:str
    needs_review:bool|None
    execution_evidence:str="not_observed"
    service_action:str="none"
    def as_dict(self):return asdict(self)

def reference_only(v,a):
    """Narrow suppression: never remove original evidence; outside actions veto demotion."""
    if not a.mentioned or not v.balanced or v.markup or a.artifact or a.explicit_act:return False
    if len(v.full)>180 or v.quotes>3 or len(v.clauses)>5:return False
    outer=NEG.sub(" ",v.outer)
    if OVERRIDE.search(outer) or AFFIRM.search(outer):return False
    if any(re.search(r"^(?:另外|此外|然后|不过|随后|接着|同时|另请)",s) and CHANGE.search(s) for s in v.clauses):
        return False
    if a.report and not (EDIT.search(outer) and PROTECT.search(outer)):return False
    if v.quotes and EDIT.search(outer):
        return bool(META.search(outer) or re.search(r"原[文句]|这[句段]|措辞|字面|引文|语气|含义",outer))
    # No de-escalation solely because someone says "for testing" or claims to be a researcher.
    return bool(RISK_TOPIC.search(outer) and PROTECT.search(outer) and
                (DOC.search(outer) or EDIT.search(outer)) and not FORMAL.search(outer)
                and not (SENSITIVE.search(outer) and CHANGE.search(outer) and ASK.search(outer)))

class Auditor:
    def __init__(self):self.base=BaselineAuditor()
    def audit(self,text):
        base=self.base.audit(text)
        if base.signal=="unknown":return Decision(base.signal,base.review,"unknown","unclear","incomplete",None)
        v=view(text)
        if v is None:
            # Parser failure may not silently demote a previously raised alert.
            if base.review=="review":return Decision(base.signal,base.review,"suspected",base.speech_act,"review",True)
            return Decision(base.signal,base.review,"unknown","unclear","incomplete",None)
        a=interpret(v,base.speech_act)
        rel=evidence(v)
        if a.artifact or rel.artifact:route="review"
        elif reference_only(v,a):route="record_only"
        elif (a.report or rel.report) and not a.mentioned:route="case_review"
        elif base.review=="review":route="review"
        elif a.mentioned:route="record_only"
        else:route="no_signal"
        # This OR applies to the audit evidence, not the user-visible false-alarm metric.
        raw=base.signal=="suspected" or a.report or a.artifact or rel.report or rel.artifact
        return Decision(base.signal,base.review,"suspected" if raw else "no_signal",a.speech,route,
                        route in ("review","case_review"))

def audit(text):
    return Auditor().audit(text)
