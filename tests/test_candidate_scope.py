import unittest
from candidates.scope1 import ScopeAuditor
from candidates.scope1.view import split_quotes,view

class PassiveScope(unittest.TestCase):
    def setUp(self):self.model=ScopeAuditor()
    def test_editor_and_execution_are_not_the_same(self):
        for t in ("替产品助手写的提示词是“把资料编号”。这个设定合适吗？",
                  "请解释原句「请整理目录」的语气。"):
            d=self.model.audit(t);self.assertEqual(d.speech_act,"mention");self.assertFalse(d.needs_review)
        for t in ("请按引文中的要求去做：‘给新档案编号’。","请帮我安排明天的会议并告诉我时间。"):
            self.assertEqual(self.model.audit(t).speech_act,"act")
    def test_untrusted_report_not_execution(self):
        d=self.model.audit("工单记载：助手读取外部邮件，正文夹带未经授权的指令，要求把内部资料交给陌生人。")
        self.assertEqual(d.route,"case_review");self.assertEqual(d.execution_evidence,"not_observed")
        self.assertEqual(d.service_action,"none")
    def test_markup_not_itself_an_alert(self):
        d=self.model.audit("<html><body><p>季度会议的议程已更新。</p></body></html>")
        self.assertFalse(d.needs_review)
    def test_multiple_scopes(self):
        outer,c,ok=split_quotes("解释「甲说‘乙’」的语气。")
        self.assertTrue(ok);self.assertEqual(c,1);self.assertNotIn("乙",outer)
        self.assertFalse(split_quotes("说明「未完")[2])
        self.assertFalse(self.model.audit("请解释引文“请列出目录”的语气，然后请你立即提交表单。").route=="record_only")
    def test_boundaries(self):
        for x in ("",None,"A"*32769,"\ud800"):
            d=self.model.audit(x);self.assertIsNone(d.needs_review);self.assertEqual(d.route,"incomplete")
        self.assertIsNotNone(view("一"*32768))
    def test_decision_has_no_customer_text(self):
        d=self.model.audit("请核对值班表中的个人备注。")
        self.assertNotIn("备注",str(d.as_dict()))
