"""Scanner for mutable default argument values in Python source."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass

PRUNE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", "target", ".tox", ".mypy_cache", ".pytest_cache",
    ".eggs",
}


@dataclass
class Finding:
    path: str
    line: int
    function: str
    param: str
    kind: str


def _mutable_kind(node: ast.AST) -> str:
    """Return a kind string if node is a mutable default, else empty."""
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        return type(node).__name__.lower()
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "dict", "set"}
        and not node.args
        and not node.keywords
    ):
        return node.func.id
    return ""


def _scan_tree(tree: ast.AST, filename: str) -> list[Finding]:
    findings: list[Finding] = []

    def handle(func_node, name: str) -> None:
        args = func_node.args
        positional = list(args.posonlyargs) + list(args.args)
        defaults = args.defaults or []
        n_default = len(defaults)
        n_pos = len(positional)
        for i, default in enumerate(defaults):
            kind = _mutable_kind(default)
            if kind:
                idx = n_pos - n_default + i
                param = positional[idx].arg if 0 <= idx < n_pos else "?"
                findings.append(Finding(
                    path=filename, line=func_node.lineno,
                    function=name, param=param, kind=kind,
                ))
        for kwarg, default in zip(args.kwonlyargs, args.kw_defaults or []):
            if default is None:
                continue
            kind = _mutable_kind(default)
            if kind:
                findings.append(Finding(
                    path=filename, line=func_node.lineno,
                    function=name, param=kwarg.arg, kind=kind,
                ))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            handle(node, node.name)
        elif isinstance(node, ast.Lambda):
            handle(node, "<lambda>")
    return findings


def _scan_source(source: str, filename: str) -> list[Finding]:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []
    return _scan_tree(tree, filename)


def scan(root: str, exclude: list[str] | None = None) -> list[Finding]:
    exclude = exclude or []
    findings: list[Finding] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in PRUNE_DIRS and d not in exclude
        ]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if any(rel == e or rel.startswith(e + os.sep) for e in exclude):
                continue
            try:
                with open(full, encoding="utf-8") as fh:
                    source = fh.read()
            except (OSError, UnicodeError):
                continue
            findings.extend(_scan_source(source, rel))
    findings.sort(key=lambda f: (f.path, f.line))
    return findings
