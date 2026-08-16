import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import ithon_run
from ithon_static import StaticTypeError


class IthonRunnerTests(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("sample_pi_module", None)
        sys.modules.pop("foreign_only", None)
        sys.meta_path[:] = [
            finder
            for finder in sys.meta_path
            if not isinstance(finder, ithon_run.IthonFinder)
        ]

    def test_finder_loads_pi_module(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample_pi_module.pi").write_text(
                "value: int = 42\n", encoding="utf-8"
            )
            sys.path.insert(0, directory)
            try:
                ithon_run._install_importer()
                module = importlib.import_module("sample_pi_module")
                self.assertEqual(module.value, 42)
                self.assertTrue(module.__file__.endswith(".pi"))
            finally:
                sys.path.remove(directory)

    def test_finder_does_not_claim_py(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "foreign_only.py").write_text("value = 42\n", encoding="utf-8")
            finder = ithon_run.IthonFinder()
            self.assertIsNone(finder.find_spec("foreign_only", [directory]))

    def test_runner_rejects_py_as_ithon_source(self):
        with self.assertRaisesRegex(SystemExit, r"\.pi; \.py is Python"):
            ithon_run.main(["program.py"])

    def test_runner_checks_before_execution(self):
        with self.assertRaises(StaticTypeError):
            ithon_run._run_source("x = 42\nx = 'bad'\n", "bad.pi", ["bad.pi"])

    def test_c_program_is_checked_and_run(self):
        ithon_run.main(["-c", "x: int = 42"])


if __name__ == "__main__":
    unittest.main()
