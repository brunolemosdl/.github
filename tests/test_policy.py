import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("policy", pathlib.Path(__file__).parent.parent / "scripts" / "policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
OWNER = "Bruno Lemos"


class Policy(unittest.TestCase):
    def test_branch(self):
        self.assertTrue(policy.BRANCH.match("feat/task-123/auth/password-reset"))
        for bad in ("feat/auth-password", "Feat/task-1/auth/x", "feat/task-1/auth/Reset", "feat/task-1/auth/reset_x"):
            self.assertFalse(policy.BRANCH.match(bad), bad)

    def test_header(self):
        self.assertEqual(policy.check_header("feat(auth): [TASK-123] add password reset functionality", "t", "123"), [])
        self.assertTrue(policy.check_header("feat: add reset", "t", None))
        self.assertTrue(policy.check_header("feat(auth): [TASK-9] add reset", "t", "123"))
        self.assertTrue(policy.check_header("feat(auth): [TASK-123] add reset.", "t", "123"))
        self.assertTrue(policy.check_header("feat(auth): [TASK-123] Add reset", "t", "123"))

    def test_message(self):
        good = "feat(auth): [TASK-1] add reset\n\n- Implement endpoint.\n- Add tests."
        self.assertEqual(policy.check_message("abc1234", good, OWNER, OWNER, "1"), [])
        self.assertEqual(policy.check_message("abc1234", "fix(ui): [TASK-1] fix a typo", OWNER, OWNER, "1"), [])
        self.assertTrue(policy.check_message("a", "feat(auth): [TASK-1] add\n- no blank line", OWNER, OWNER, "1"))
        self.assertTrue(policy.check_message("a", good + "\n\nCo-Authored-By: Someone <x@y>", OWNER, OWNER, "1"))
        self.assertTrue(policy.check_message("a", good, "someone else", OWNER, "1"))
        self.assertTrue(policy.check_message("a", "feat(auth): [TASK-1] add\n\n- Generated with Claude Code", OWNER, OWNER, "1"))
        self.assertEqual(policy.check_message("a", "feat(ci): [TASK-1] add\n\n- Run Claude Code in a container", OWNER, OWNER, "1"), [])

    def test_added_lines(self):
        diff = "+++ b/README.md\n+a line — with a dash\n+++ b/app.py\n+key = 'ghp_" + "a" * 36 + "'\n+++ b/ok.md\n+fine, a comma"
        errs = policy.check_added(diff)
        self.assertEqual(len(errs), 2)
        self.assertTrue(any("em dash" in e for e in errs) and any("GitHub token" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
