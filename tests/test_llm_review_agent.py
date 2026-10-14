import unittest
from unittest.mock import patch

from src.comment_generator import CommentItem
from src.llm_review_agent import review_generated_comments


class TestLLMReviewAgent(unittest.TestCase):
    def test_revises_summary_and_preserves_ast_sections(self):
        source = "def add(left: int, right: int) -> int:\n    return left + right\n"
        comment = CommentItem(
            node_id="function_add",
            node_type="function",
            lineno=1,
            col_offset=0,
            text='"""\nAdds left and right.\n\nArgs:\n    left (int): Left.\n"""',
            kind="docstring",
            target_name="add",
        )

        with patch("src.llm_review_agent._request_review", return_value=[
            {"node_id": "function_add", "summary": "Returns the sum of two integers."}
        ]) as request_review:
            result = review_generated_comments([comment], source)

        self.assertEqual(result[0].text.splitlines()[1], "Returns the sum of two integers.")
        self.assertIn("Args:\n    left (int): Left.", result[0].text)
        self.assertIn("def add", request_review.call_args.args[0][0]["code"])
        self.assertEqual(comment.text.splitlines()[1], "Adds left and right.")

    def test_ignores_invalid_summaries_and_non_docstrings(self):
        source = "def add(left, right):\n    return left + right\n"
        docstring = CommentItem(
            "function_add", "function", 1, 0, '"""\nAdds values.\n"""', "docstring", "add"
        )
        inline = CommentItem("inline_add", "inline", 1, 0, "# note", "inline", "add")

        with patch("src.llm_review_agent._request_review", return_value=[
            {"node_id": "function_add", "summary": "Invalid\nsecond line"},
            {"node_id": "unknown", "summary": "Unrelated."},
        ]) as request_review:
            result = review_generated_comments([docstring, inline], source)

        self.assertEqual(result, [docstring, inline])
        request_review.assert_called_once()

    def test_skips_request_when_there_are_no_docstrings(self):
        with patch("src.llm_review_agent._request_review") as request_review:
            result = review_generated_comments([], "x = 1\n")

        self.assertEqual(result, [])
        request_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()