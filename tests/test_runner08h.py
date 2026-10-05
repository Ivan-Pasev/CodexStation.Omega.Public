import json, subprocess, tempfile, unittest
from pathlib import Path

import runner08h.run_source as runner

class Runner08HTests(unittest.TestCase):
    def make_repo(self):
        td=tempfile.TemporaryDirectory()
        root=Path(td.name)
        subprocess.run(["git","init","-q"],cwd=root,check=True)
        subprocess.run(["git","config","user.email","test@example.invalid"],cwd=root,check=True)
        subprocess.run(["git","config","user.name","Runner Test"],cwd=root,check=True)
        (root/"tracked.txt").write_text("x\n")
        subprocess.run(["git","add","tracked.txt"],cwd=root,check=True)
        subprocess.run(["git","commit","-qm","fixture"],cwd=root,check=True)
        sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
        return td,root,sha

    def test_exact_pin_clean_pass(self):
        td,root,sha=self.make_repo()
        try:
            old=runner.FAMILIES.get("TEST")
            runner.FAMILIES["TEST"]={"repository":"fixture/test","source_commit":sha,"scope":"TEST","steps":[{"id":"ok","cwd":".","command":"true"}]}
            receipt=runner.run("TEST",root,"TEST","1","runner")
            self.assertEqual(receipt["overall_status"],"PASS")
            self.assertFalse(receipt["source_tree_modified_for_test"])
        finally:
            if old is None: runner.FAMILIES.pop("TEST",None)
            else: runner.FAMILIES["TEST"]=old
            td.cleanup()

    def test_wrong_pin_fails_preflight(self):
        td,root,sha=self.make_repo()
        try:
            old=runner.FAMILIES.get("TEST")
            runner.FAMILIES["TEST"]={"repository":"fixture/test","source_commit":"0"*40,"scope":"TEST","steps":[{"id":"ok","cwd":".","command":"true"}]}
            receipt=runner.run("TEST",root,"TEST","2","runner")
            self.assertEqual(receipt["overall_status"],"FAIL")
            self.assertIn("SOURCE_COMMIT_MISMATCH",receipt["execution_metadata"]["preflight_errors"])
        finally:
            if old is None: runner.FAMILIES.pop("TEST",None)
            else: runner.FAMILIES["TEST"]=old
            td.cleanup()

    def test_source_mutation_is_detected(self):
        td,root,sha=self.make_repo()
        try:
            old=runner.FAMILIES.get("TEST")
            runner.FAMILIES["TEST"]={"repository":"fixture/test","source_commit":sha,"scope":"TEST","steps":[{"id":"mutate","cwd":".","command":"printf y >> tracked.txt"}]}
            receipt=runner.run("TEST",root,"TEST","3","runner")
            self.assertEqual(receipt["overall_status"],"FAIL")
            self.assertTrue(receipt["source_tree_modified_for_test"])
            self.assertIn("SOURCE_TREE_CHANGED_DURING_RUN",receipt["execution_metadata"]["preflight_errors"])
        finally:
            subprocess.run(["git","checkout","--","tracked.txt"],cwd=root)
            if old is None: runner.FAMILIES.pop("TEST",None)
            else: runner.FAMILIES["TEST"]=old
            td.cleanup()

if __name__=="__main__":
    unittest.main()
