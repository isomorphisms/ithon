"""Strict Ithon program runner."""

from __future__ import annotations

import importlib.abc
import importlib.util
import os
import sys
import traceback
from pathlib import Path

from ithon_static import StaticTypeError, check_source


class IthonSourceLoader(importlib.abc.SourceLoader):
    def __init__(self, fullname: str, path: str) -> None:
        self.fullname = fullname
        self.path = path

    def get_filename(self, fullname: str) -> str:
        return self.path

    def get_data(self, path: str) -> bytes:
        with open(path, "rb") as handle:
            return handle.read()

    def source_to_code(self, data: bytes, path: str, *, _optimize: int = -1):
        source = data.decode("utf-8")
        check_source(source, path)
        return compile(source, path, "exec", dont_inherit=True, optimize=_optimize)


class IthonFinder(importlib.abc.MetaPathFinder):
    """Load .ithon modules as strict Ithon while leaving .py as foreign Python."""

    def find_spec(self, fullname: str, path=None, target=None):
        search = sys.path if path is None else path
        leaf = fullname.rpartition(".")[2]
        for entry in search:
            base = Path(entry or os.getcwd())
            module = base / f"{leaf}.ithon"
            if module.is_file():
                loader = IthonSourceLoader(fullname, str(module))
                return importlib.util.spec_from_file_location(fullname, module, loader=loader)
            package = base / leaf / "__init__.ithon"
            if package.is_file():
                loader = IthonSourceLoader(fullname, str(package))
                return importlib.util.spec_from_file_location(
                    fullname,
                    package,
                    loader=loader,
                    submodule_search_locations=[str(package.parent)],
                )
        return None


def _install_importer() -> None:
    if not any(isinstance(finder, IthonFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, IthonFinder())


def _run_source(source: str, filename: str, argv: list[str]) -> None:
    check_source(source, filename)
    code = compile(source, filename, "exec")
    sys.argv = argv
    if filename not in {"<string>", "<stdin>"}:
        sys.path[0] = os.path.dirname(os.path.abspath(filename))
    namespace = {
        "__name__": "__main__",
        "__file__": filename,
        "__package__": None,
        "__cached__": None,
        "__builtins__": __builtins__,
    }
    exec(code, namespace, namespace)


def main() -> None:
    _install_importer()
    args = sys.argv[1:]
    if not args:
        raise SystemExit("ithon: strict interactive mode is not implemented; give a file or -c program")
    if args[0] == "-c":
        if len(args) < 2:
            raise SystemExit("ithon: -c requires an argument")
        _run_source(args[1], "<string>", ["-c", *args[2:]])
        return
    if args[0].startswith("-"):
        raise SystemExit(f"ithon: {args[0]} is not supported in strict mode yet")
    path = args[0]
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    _run_source(source, path, [path, *args[1:]])


if __name__ == "__main__":
    try:
        main()
    except StaticTypeError as exc:
        sys.stderr.writelines(traceback.format_exception_only(exc))
        raise SystemExit(1) from None
