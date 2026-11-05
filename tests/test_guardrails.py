import unittest

from askdb import guardrails


class TestReadOnly(unittest.TestCase):
    def test_select_is_allowed(self):
        guardrails.check_sql("SELECT COUNT(*) FROM Invoice")

    def test_cte_is_allowed(self):
        guardrails.check_sql("WITH x AS (SELECT 1) SELECT * FROM x")

    def test_writes_are_refused(self):
        for sql in ("DELETE FROM Customer", "SELECT 1; DROP TABLE Invoice", "UPDATE Invoice SET Total = 0"):
            with self.assertRaises(ValueError):
                guardrails.check_sql(sql)


class TestLimits(unittest.TestCase):
    def test_long_questions_are_refused(self):
        self.assertIsNotNone(guardrails.check_question("x" * (guardrails.MAX_QUESTION_CHARS + 1)))

    def test_results_are_capped(self):
        _, rows = guardrails.filter_result(["n"], [(i,) for i in range(guardrails.MAX_ROWS + 5)])
        self.assertEqual(len(rows), guardrails.MAX_ROWS)
