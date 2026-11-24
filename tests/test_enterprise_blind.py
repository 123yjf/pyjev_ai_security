"""Logic tests do not require ML dependencies or any network calls."""
import json
import unittest
from research.enterprise.common import HERE
from research.enterprise.prepare import item, overlap
from research.enterprise.infer import windows
from research.enterprise.score import evaluate, decisions

def pred(i, route, p, shadow=None):
    return dict(id=i,pyjev=route,shadow=shadow or route,p=p)

class PairedBlindTests(unittest.TestCase):
    def test_complete_coverage_at_window_edges(self):
        for n in (0,1,510,511,956,957,2000):
            ids=list(range(n))
            ws=list(windows(ids))
            self.assertEqual(set().union(*(set(w) for w in ws)),set(ids))
            self.assertTrue(all(len(w)<=510 for w in ws))
            for a,b in zip(ws,ws[1:]): self.assertEqual(a[-64:],b[:64])
    def test_wrongness_and_abstentions_do_not_become_negatives(self):
        gs=[dict(id="x",label=1,strata=["s"]),dict(id="y",label=0,strata=["s"]),dict(id="z",label=0,strata=["s"])]
        ps=[pred("x","no_signal",.5),pred("y","incomplete",.7),pred("z","no_signal",.005)]
        a=evaluate(gs,ps)["s"]
        self.assertEqual(a["paired"]["positive"]["only_pyjev_wrong"],1)
        self.assertEqual(a["paired"]["negative"]["incomplete"],1)
        self.assertEqual(a["modes"]["pyjev"]["tn"],1)
        self.assertEqual(a["modes"]["hikma_0005"]["fp"],2)
        self.assertEqual(decisions(pred("z","review",.004,"record_only")),(1,0,0,0))
        with self.assertRaises(ValueError):evaluate(gs,ps[:-1])
        with self.assertRaises(ValueError):evaluate(gs,ps+ps[:1])
    def test_history_filter_and_internal_duplicates(self):
        xs=[item("x",i,s,0,["s"]) for i,s in enumerate(("ＡＡ１２","aa12","独立的短句","这是一段非常普通的天气播报现在到下午中午气温上升"))]
        keep,r=overlap(xs,[("hist",["这是一段非常普通的天气播报现在到下午中午气温下降"])])
        self.assertEqual(keep,{2});self.assertEqual(r["internal_exact_rows"],2)
        self.assertEqual(r["reference"]["hist"]["near_only"],1)
    def test_sealed_subgroups(self):
        c=json.loads((HERE/"cohort.json").read_text())
        self.assertEqual(c["retained_rows"],sum(c["strata"][k] for k in ("docs","direct","agent")))
        self.assertEqual(c["strata"]["mention_or_quote"],c["strata"]["risk_discussion"]+c["strata"]["quoted_design"])

if __name__=="__main__":unittest.main()
