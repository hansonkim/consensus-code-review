"""
Command line interface for the consensus-code-review package.

The CLI exposes a small set of sub-commands that make it easy to run the MCP
stdio server or inspect the available tools after the package is installed
from PyPI. This module is intentionally lightweight so it can be executed via
`uvx` or the console script defined in pyproject.toml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from . import get_version
from .mcp import MCPManager
from .stdio_server import run_stdio_server


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consensus-code-review",
        description="Run the Consensus Code Review MCP server or inspect its tools.",
    )
    subparsers = parser.add_subparsers(dest="command")

    server_parser = subparsers.add_parser(
        "server",
        help="Run the MCP stdio server (default).",
    )
    server_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional path for the MCP server log file (defaults to logs/mcp_server.log).",
    )

    tools_parser = subparsers.add_parser(
        "tools",
        help="List the available MCP tools.",
    )
    tools_parser.add_argument(
        "--json",
        action="store_true",
        help="Output the tool list as machine-readable JSON.",
    )

    subparsers.add_parser("version", help="Display the installed package version.")

    parser.set_defaults(command="server")
    return parser


def _handle_server(log_file: Path | None) -> None:
    run_stdio_server(log_path=log_file)


def _handle_tools(output_json: bool) -> None:
    manager = MCPManager()
    tools = manager.get_all_tools()
    if output_json:
        json.dump(tools, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        description = manager.generate_tool_description()
        print(description)


def _handle_version() -> None:
    print(get_version())


def app(argv: Iterable[str] | None = None) -> None:
    """Entry point for console script and `python -m consensus_code_review`."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "server":
        _handle_server(args.log_file)
    elif args.command == "tools":
        _handle_tools(args.json)
    elif args.command == "version":
        _handle_version()
    else:  # pragma: no cover - argparse prevents reaching this
        parser.error(f"Unknown command: {args.command}")
