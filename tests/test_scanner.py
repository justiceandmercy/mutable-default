"""Tests for mutable-default scanner."""

import textwrap
from pathlib import Path

from mutable_default import scanner


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


def test_detects_list_default(tmp_path):
    _write(tmp_path, "a.py", """
        def f(x=[]):
            return x
    """)
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 1
    assert hits[0].function == "f"
    assert hits[0].param == "x"
    assert hits[0].kind == "list"


def test_detects_dict_and_set(tmp_path):
    _write(tmp_path, "a.py", """
        def g(y={}):
            pass
        def h(z=set()):
            pass
    """)
    hits = scanner.scan(str(tmp_path))
    kinds = {h.kind for h in hits}
    assert kinds == {"dict", "set"}


def test_kwonly_default(tmp_path):
    _write(tmp_path, "a.py", """
        def f(*, items=[]):
            return items
    """)
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 1
    assert hits[0].param == "items"


def test_async_function(tmp_path):
    _write(tmp_path, "a.py", """
        async def f(x=[]):
            return x
    """)
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 1


def test_lambda(tmp_path):
    _write(tmp_path, "a.py", """
        f = lambda x=[]: x
    """)
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 1
    assert hits[0].function == "<lambda>"


def test_clean_code(tmp_path):
    _write(tmp_path, "a.py", """
        def f(x=None):
            if x is None:
                x = []
            return x
    """)
    assert scanner.scan(str(tmp_path)) == []


def test_immutable_defaults_ok(tmp_path):
    _write(tmp_path, "a.py", """
        def f(x=(), y="", z=0, w=None, v=frozenset()):
            return x, y, z, w, v
    """)
    assert scanner.scan(str(tmp_path)) == []


def test_call_defaults(tmp_path):
    _write(tmp_path, "a.py", """
        def f(x=list(), y=dict(), z=set()):
            return x, y, z
    """)
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 3


def test_excludes_dirs(tmp_path):
    d = tmp_path / "venv"
    d.mkdir()
    (d / "a.py").write_text("def f(x=[]):\n    pass\n")
    (tmp_path / "b.py").write_text("def g(y=[]):\n    pass\n")
    hits = scanner.scan(str(tmp_path))
    assert len(hits) == 1
    assert hits[0].param == "y"


def test_syntax_error_skipped(tmp_path):
    (tmp_path / "bad.py").write_text("def f(x=[]\n")
    assert scanner.scan(str(tmp_path)) == []


def test_cli_exit_code(tmp_path):
    _write(tmp_path, "a.py", "def f(x=[]):\n    pass\n")
    from mutable_default.cli import main
    assert main([str(tmp_path)]) == 1
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "b.py").write_text("def g(x=None):\n    pass\n")
    assert main([str(clean)]) == 0


def test_json_output(tmp_path, capsys):
    _write(tmp_path, "a.py", "def f(x=[]):\n    pass\n")
    from mutable_default.cli import main
    rc = main([str(tmp_path), "--format", "json"])
    assert rc == 1
    out = capsys.readouterr().out
    assert '"param": "x"' in out
