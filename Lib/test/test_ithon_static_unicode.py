import unittest

from ithon_static import StaticTypeError, check_source


class UnicodeStaticTypingTests(unittest.TestCase):
    def test_left_arrow_assignment_infers_and_preserves_type(self):
        check_source("x ← 42\nx ← 43")
        with self.assertRaisesRegex(StaticTypeError, "expects int, got str"):
            check_source("x ← 42\nx ← 'forty two'")

    def test_annotated_left_arrow_assignment(self):
        check_source("x: int ← 42")
        with self.assertRaisesRegex(StaticTypeError, "expected int, got str"):
            check_source("x: int ← 'forty two'")

    def test_unicode_lambda_and_multiplication_use_callable_context(self):
        check_source(
            "from typing import Callable\n"
            "double: Callable[[int], int] ← λ x: x × 2\n"
            "answer ← double(21)\n"
        )


if __name__ == "__main__":
    unittest.main()
