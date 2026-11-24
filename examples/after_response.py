"""Try: python -m pip install . && python examples/after_response.py"""
from pyjev import Auditor

auditor = Auditor()
for text in ("请解释“给资料编号”这句话的语气。", "请你照做：“给资料编号”。", "“给资料编号”"):
    result = auditor.audit(text)
    print(result.as_dict())  # The submitted text is not included in the record.
# Application developers decide where to store these annotations. No sender or blocker is provided.
