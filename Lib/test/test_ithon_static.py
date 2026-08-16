import unittest

from ithon_static import StaticTypeError, check_source


class MandatoryStaticTypingTests(unittest.TestCase):
    def check_ok(self, source):
        check_source(source)

    def check_bad(self, source, text):
        with self.assertRaisesRegex(StaticTypeError, text):
            check_source(source)

    def test_assignment_infers_type(self):
        self.check_ok("x = 40 + 2\nx = 43")

    def test_assignment_cannot_change_type(self):
        self.check_bad("x = 42\nx = 'forty two'", "expects int, got str")

    def test_annotation_accepts_numeric_widening(self):
        self.check_ok("x: float = 42")

    def test_annotation_rejects_wrong_type(self):
        self.check_bad("x: int = 4.2", "expected int, got float")

    def test_function_parameters_are_typed(self):
        self.check_bad("def f(x) -> int:\n    return 1", "parameter 'x' needs a static type")

    def test_function_return_is_typed(self):
        self.check_bad("def f(x: int):\n    return x", "function 'f' needs a return type")

    def test_return_type_is_checked(self):
        self.check_bad("def f(x: int) -> int:\n    return 'x'", "expected int, got str")

    def test_local_function_call_is_checked(self):
        self.check_bad(
            "def double(x: int) -> int:\n"
            "    return x * 2\n"
            "answer = double('21')",
            "expected int, got str",
        )

    def test_lambda_requires_callable_context(self):
        self.check_bad("double = lambda x: x * 2", "lambda needs a contextual Callable")

    def test_lambda_uses_callable_context(self):
        self.check_ok("double: Callable[[int], int] = lambda x: x * 2\nanswer = double(21)")

    def test_external_unknown_result_needs_annotation(self):
        self.check_bad("import math\nx = math.sqrt(4.0)", "cannot infer assignment type")
        self.check_ok("import math\nx: float = math.sqrt(4.0)")

    def test_for_loop_infers_from_range(self):
        self.check_ok("total = 0\nfor i in range(4):\n    total = total + i")

    def test_empty_container_needs_context(self):
        self.check_bad("xs = []", "empty list needs an explicit element type")
        self.check_ok("xs: list[int] = []")


if __name__ == "__main__":
    unittest.main()
