import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from pyjev.cli import MAX_WIRE,bounded_lines

ROOT=Path(__file__).resolve().parents[1]
def cli(*args,data=b""):
    return subprocess.run([sys.executable,"-B","-m","pyjev",*args],input=data,capture_output=True,cwd=ROOT,timeout=25)

class Commands(unittest.TestCase):
    def test_version_and_help(self):
        self.assertIn("0.1.0",cli("--version").stdout.decode())
        for cmd in ("scan","quiz","batch","bench","metrics","doctor"):
            self.assertIn(cmd,cli("--help").stdout.decode())

    def test_sdk_cli_consistency(self):
        from pyjev import audit
        s="请解释“给资料编号”这句话的语气。"
        for args in (("-p",s,"--json"),("scan","--json",s),("--json","scan",s)):
            q=cli(*args);self.assertEqual(q.returncode,0);self.assertEqual(json.loads(q.stdout),audit(s).as_dict())

    def test_scan_multiline_and_limits(self):
        q=cli("scan","-","--json",data="材料甲\n材料乙".encode());self.assertEqual(q.returncode,0);self.assertIn("signal",json.loads(q.stdout))
        bad=cli("scan","--json",data=b"\xff");self.assertEqual(bad.returncode,2)
        bad=cli("scan","--json",data=b"z"*(MAX_WIRE+1));self.assertEqual(bad.returncode,2)

    def test_crlf_wire_boundary_and_recovery(self):
        stream=io.BytesIO(b"a"*MAX_WIRE+b"\r\n"+b"b"*(3*MAX_WIRE)+b"\nnext\n")
        v=list(bounded_lines(stream));self.assertEqual((len(v[0][0]),v[0][1]),(MAX_WIRE,None))
        self.assertEqual(v[1:],[(None,"wire_limit"),("next",None)])

    def test_jsonl_malformed_non_echo_nonzero(self):
        q=cli("batch",data=b'{"text":"redacted-canary"}\nmalformed-secret\n{"text":"next"}\n{"text":3}\n{"extra":1,"text":"ok"}\n')
        v=[json.loads(s) for s in q.stdout.splitlines()];self.assertEqual(q.returncode,2);self.assertEqual([r["line"] for r in v],[1,2,3,4,5])
        self.assertEqual(v[1]["error"],"invalid_json");self.assertIn("audit",v[2]);self.assertEqual(v[4]["error"],"expected_text_object")
        self.assertNotIn(b"canary",q.stdout+q.stderr);self.assertNotIn(b"malformed-secret",q.stdout+q.stderr)

    def test_pipe_not_repl(self):
        q=cli(data=b"/exit\n/demo\n");self.assertEqual(len(q.stdout.splitlines()),2)
        self.assertTrue(all("audit" in json.loads(l) for l in q.stdout.splitlines()))

    def test_duplicate_field_is_not_last_value_wins(self):
        q=cli("batch",data=b'{"text":"one","text":"two"}\n')
        self.assertEqual(q.returncode,2);self.assertEqual(json.loads(q.stdout),{"line":1,"error":"duplicate_field"})

    def test_quiz_and_repl(self):
        q=cli("quiz","--rounds","1","--seed","7",data=b"invalid\n1\n")
        self.assertEqual(q.returncode,0);self.assertIn("作者标注",q.stdout.decode())
        q=cli("-i",data=b"/help\n/reset\n/exit\n");self.assertEqual(q.returncode,0);self.assertIn("计数归零",q.stdout.decode())

    def test_demo_and_authored_fixtures(self):
        q=cli("demo");self.assertEqual(q.returncode,0)
        self.assertIn(b"record_only",q.stdout)
        q=cli("batch","examples/office.jsonl");self.assertEqual(q.returncode,0);self.assertEqual(len(q.stdout.splitlines()),3)

    def test_stored_vs_live_reports(self):
        self.assertEqual(json.loads(cli("doctor","--json").stdout)["model_checksums"],"ok")
        r=json.loads(cli("bench","--json").stdout);self.assertTrue(r["matches_frozen_evidence"])
        r=json.loads(cli("--json","metrics").stdout);self.assertEqual(r["external"]["missed"],92)
        self.assertEqual(r["source"],"frozen_aggregate_not_a_rerun")

    def test_bad_options_and_missing_file(self):
        for args in (("-i","--json"),("quiz","--rounds","10"),("batch","does-not-exist.jsonl")):
            self.assertEqual(cli(*args).returncode,2)

if __name__=="__main__":unittest.main()
