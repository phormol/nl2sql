import unittest

# sitecustomize at repo root should put ./src into sys.path automatically
from nl2sql_agent.db import ensure_limit, is_safe_select


class TestDbHelpers(unittest.TestCase):
    def test_ensure_limit_adds_when_missing(self):
        sql = "select * from t"
        out = ensure_limit(sql)
        self.assertTrue(out.lower().endswith(" limit 50"))

    def test_ensure_limit_handles_semicolon(self):
        sql = "select * from t;"
        out = ensure_limit(sql)
        self.assertEqual(out.lower(), "select * from t limit 50")

    def test_ensure_limit_respects_existing(self):
        for q in [
            "select * from t limit 5",
            "select * from t LIMIT 5;",
            "select * from t\nlimit 5",
        ]:
            out = ensure_limit(q)
            self.assertIn("limit 5", out.lower())
            self.assertNotIn("limit 50", out.lower())

    def test_is_safe_select_accepts_simple_select(self):
        self.assertTrue(is_safe_select("select 1"))

    def test_is_safe_select_rejects_semicolon(self):
        # Semicolon is blocked to avoid multiple statements
        self.assertFalse(is_safe_select("select 1;"))

    def test_is_safe_select_rejects_dml(self):
        self.assertFalse(is_safe_select("delete from t where 1=1"))
        self.assertFalse(is_safe_select("insert into t values (1)"))


if __name__ == "__main__":
    unittest.main()
