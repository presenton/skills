#!/usr/bin/env python3
"""Search Presenton designs, export HTML, and return export URLs."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from validate_html import validate_html


DEFAULT_API_BASE = "https://api.presenton.ai"
SEARCH_TIMEOUT_SECONDS = 60.0
EXPORT_TIMEOUT_SECONDS = 300.0
TEMP_MARKER_NAME = ".presenton-temp"
TEMP_MARKER_CONTENT = "presenton-owned\n"


class PresentonError(RuntimeError):
    pass


def print_status(message: str) -> None:
    print(f"[presenton] {message}", file=sys.stderr, flush=True)


@contextmanager
def status_heartbeat(message: str, interval_seconds: float = 10.0) -> Iterator[None]:
    print_status(message)
    stopped = threading.Event()

    def emit_heartbeat() -> None:
        while not stopped.wait(interval_seconds):
            print_status(f"{message} (still working)")

    thread = threading.Thread(target=emit_heartbeat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join()


def request_json(
    endpoint: str,
    payload: dict[str, Any],
    timeout: float = 300.0,
) -> Any:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "presenton-skill/1",
    }
    request = urllib.request.Request(
        f"{DEFAULT_API_BASE}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with status_heartbeat(f"Waiting for {endpoint}"):
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        print_status(f"Received response from {endpoint}")
        return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            error_payload = json.loads(body)
            detail = error_payload.get("detail") or error_payload.get("error") or body
        except json.JSONDecodeError:
            detail = body
        raise PresentonError(f"Presenton API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise PresentonError(f"Could not reach Presenton API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise PresentonError("Presenton API returned invalid JSON") from exc


def get_temp_root() -> Path:
    return Path(tempfile.gettempdir()).resolve(strict=True)


def resolve_owned_temp_dir(path: Path) -> Path:
    if path.expanduser().is_symlink():
        raise PresentonError("Refusing to clean up a symbolic link")
    try:
        resolved = path.expanduser().resolve(strict=True)
        temp_root = get_temp_root()
        resolved.relative_to(temp_root)
    except (OSError, ValueError) as exc:
        raise PresentonError("Temporary directory is outside the OS temporary root") from exc
    if resolved == temp_root:
        raise PresentonError("Refusing to clean up the OS temporary root")
    if resolved.parent != temp_root or not resolved.name.startswith("presenton-"):
        raise PresentonError("Temporary directory was not created by Presenton")
    if not resolved.is_dir():
        raise PresentonError("Presenton temporary path is not a directory")
    marker = resolved / TEMP_MARKER_NAME
    if marker.is_symlink() or not marker.is_file():
        raise PresentonError("Presenton temporary ownership marker is missing")
    try:
        marker_content = marker.read_text(encoding="utf-8")
    except OSError as exc:
        raise PresentonError("Could not read Presenton temporary ownership marker") from exc
    if marker_content != TEMP_MARKER_CONTENT:
        raise PresentonError("Presenton temporary ownership marker is invalid")
    return resolved


def command_create_temp(_: argparse.Namespace) -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="presenton-")).resolve(strict=True)
    (temp_dir / TEMP_MARKER_NAME).write_text(TEMP_MARKER_CONTENT, encoding="utf-8")
    print_status(f"Created temporary workspace {temp_dir}")
    print(temp_dir)
    return 0


def command_cleanup_temp(args: argparse.Namespace) -> int:
    temp_dir = resolve_owned_temp_dir(args.path)
    shutil.rmtree(temp_dir)
    print_status(f"Cleaned temporary workspace {temp_dir}")
    return 0


def command_search(args: argparse.Namespace) -> int:
    print_status("Searching for matching presentation designs")
    results = request_json(
        "/api/v3/designs/search",
        {"query": args.query, "n": 4},
        timeout=SEARCH_TIMEOUT_SECONDS,
    )
    if not isinstance(results, list):
        raise PresentonError("Design search returned an unexpected response")
    print_status(f"Found {len(results)} design option(s)")
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.get('title', 'Untitled')} (id={result.get('id', '?')})")
        print(f"   {result.get('description', '')}")
    return 0


def command_export(args: argparse.Namespace) -> int:
    try:
        html_path = args.html.expanduser().resolve(strict=True)
        temp_root = get_temp_root()
        relative_path = html_path.relative_to(temp_root)
        if len(relative_path.parts) < 2 or not relative_path.parts[0].startswith(
            "presenton-"
        ):
            raise ValueError
        owned_temp_dir = temp_root / relative_path.parts[0]
        resolve_owned_temp_dir(owned_temp_dir)
    except (OSError, ValueError) as exc:
        raise PresentonError(
            "Presentation HTML must be inside a directory created by create-temp"
        ) from exc

    print_status(f"Reading temporary presentation HTML from {html_path}")
    try:
        html = html_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PresentonError(f"Could not read HTML file: {exc}") from exc
    print_status("Validating HTML, Tailwind, and Chart.js requirements")
    validation_errors = validate_html(html)
    if validation_errors:
        formatted = "\n".join(f"- {error}" for error in validation_errors)
        raise PresentonError(f"HTML preflight failed:\n{formatted}")

    print_status("HTML validation passed")
    payload: dict[str, Any] = {"html": html, "format": args.format}
    if args.title:
        payload["title"] = args.title
    print_status(f"Submitting {args.format.upper()} export")
    response = request_json(
        "/api/v3/export/html-to-any",
        payload,
        timeout=EXPORT_TIMEOUT_SECONDS,
    )
    url = response.get("url") if isinstance(response, dict) else None
    parsed_url = urlparse(url) if isinstance(url, str) else None
    if (
        parsed_url is None
        or parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
    ):
        raise PresentonError("Export response did not contain a valid HTTP or HTTPS URL")
    print_status(f"{args.format.upper()} export URL is ready")
    print(url)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_temp = subparsers.add_parser(
        "create-temp", help="Create a private Presenton temporary workspace"
    )
    create_temp.set_defaults(handler=command_create_temp)

    cleanup_temp = subparsers.add_parser(
        "cleanup-temp", help="Remove a Presenton temporary workspace"
    )
    cleanup_temp.add_argument("--path", type=Path, required=True)
    cleanup_temp.set_defaults(handler=command_cleanup_temp)

    search = subparsers.add_parser("search-designs", help="Search Presenton visual designs")
    search.add_argument("--query", required=True)
    search.set_defaults(handler=command_search)

    export = subparsers.add_parser("export", help="Export compatible HTML")
    export.add_argument("--html", type=Path, required=True)
    export.add_argument("--format", choices=("pptx", "pdf", "png"), required=True)
    export.add_argument("--title")
    export.set_defaults(handler=command_export)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (PresentonError, FileNotFoundError, PermissionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
