"""mutable_default: detect mutable default argument values in Python code."""

__version__ = "0.1.0"
__all__ = ["Finding", "__version__", "scan"]

try:
    from .scanner import Finding, scan
except ImportError:  # pragma: no cover - script usage
    from scanner import Finding, scan
