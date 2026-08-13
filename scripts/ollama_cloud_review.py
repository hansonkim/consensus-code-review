#!/usr/bin/env python3
"""Run a read-only review prompt through Ollama Cloud without exposing its API key."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "glm-5.2:cloud"
DEFAULT_URL = "https://ollama.com/api/chat"
SYSTEM_PROMPT = (
    "You are a senior code reviewer. Review only the supplied artifact and contract. "
    "Do not request tools, edit files, or invent repository context."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt_file", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("~/.hermes/.env").expanduser(),
        help="fallback dotenv file used only when OLLAMA_API_KEY is absent",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("OLLAMA_CLOUD_URL", DEFAULT_URL),
    )
    return parser.parse_args()


def read_dotenv_value(path: Path, name: str) -> str | None:
    if not path.is_file():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, separator, value = line.partition("=")
        if separator and key.strip() == name:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            return value or None
    return None


def create_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        certifi = None
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    for candidate in (
        Path("/etc/ssl/cert.pem"),
        Path("/etc/ssl/certs/ca-certificates.crt"),
    ):
        if candidate.is_file():
            return ssl.create_default_context(cafile=str(candidate))
    return ssl.create_default_context()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("OLLAMA_API_KEY") or read_dotenv_value(
        args.env_file, "OLLAMA_API_KEY"
    )
    if not api_key:
        print("OLLAMA_API_KEY is not configured", file=sys.stderr)
        return 2

    prompt = args.prompt_file.read_text(encoding="utf-8")
    payload = json.dumps(
        {
            "model": args.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
    ).encode("utf-8")
    request = Request(
        args.url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "consensus-code-review/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=args.timeout,
            context=create_ssl_context(),
        ) as response:
            result = json.load(response)
    except HTTPError as error:
        print(f"Ollama Cloud HTTP error: {error.code}", file=sys.stderr)
        return 1
    except URLError as error:
        print(
            f"Ollama Cloud transport error: {type(error.reason).__name__}",
            file=sys.stderr,
        )
        return 1
    except (TimeoutError, json.JSONDecodeError) as error:
        print(f"Ollama Cloud response error: {type(error).__name__}", file=sys.stderr)
        return 1

    content = result.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        print("Ollama Cloud response did not contain message.content", file=sys.stderr)
        return 1

    print(content.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
