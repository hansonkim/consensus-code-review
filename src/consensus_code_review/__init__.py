"""
Consensus Code Review public package interface.

This module exposes the main entry points that are useful when the project is
installed from PyPI. Downstream consumers can import the MCP orchestration
utilities directly from here instead of relying on the internal package
layout.
"""

from importlib.metadata import PackageNotFoundError, version

from .mcp import MCPManager, ReviewOrchestrator

__all__ = [
    "MCPManager",
    "ReviewOrchestrator",
    "get_version",
    "main",
]


def get_version() -> str:
    """Return the installed package version."""
    try:
        return version("consensus-code-review")
    except PackageNotFoundError:  # pragma: no cover - fallback for editable installs
        return "0.0.0"


def main() -> None:
    """Entry point used by the console script."""
    from .cli import app

    app()
