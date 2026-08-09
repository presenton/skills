#!/usr/bin/env python3
"""Validate the structural contract required by Presenton's html-to-any exporter."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class PresentationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.wrapper_count = 0
        self.wrapper_depth: int | None = None
        self.slide_count = 0
        self.direct_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        is_wrapper = attributes.get("id") == "presentation-slides-wrapper"
        if is_wrapper:
            self.wrapper_count += 1
            if self.wrapper_depth is None:
                self.wrapper_depth = len(self.stack)
        elif self.wrapper_depth is not None and len(self.stack) == self.wrapper_depth + 1:
            self.slide_count += 1
        self.stack.append((tag, is_wrapper))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        popped_tag, was_wrapper = self.stack.pop()
        if was_wrapper:
            self.wrapper_depth = None
        elif popped_tag != tag:
            # HTMLParser is permissive. The browser will repair malformed markup,
            # so leave detailed nesting diagnostics to a browser-based inspection.
            return

    def handle_data(self, data: str) -> None:
        if (
            self.wrapper_depth is not None
            and len(self.stack) == self.wrapper_depth + 1
            and data.strip()
        ):
            self.direct_text = True


def validate_html(html: str) -> list[str]:
    errors: list[str] = []
    lowered = html.lower()
    for required in ("<!doctype html", "<html", "<head", "<body"):
        if required not in lowered:
            errors.append(f"Missing required document marker: {required}.")

    if "https://cdn.tailwindcss.com" not in lowered:
        errors.append("Missing required Tailwind CDN script.")
    if re.search(r"\sstyle\s*=", html, re.I):
        errors.append("Use Tailwind classes instead of inline style attributes.")
    if re.search(r"<style(?:\s|>)", html, re.I):
        errors.append("Use Tailwind classes instead of embedded style blocks.")
    if "<canvas" in lowered and "https://cdn.jsdelivr.net/npm/chart.js" not in lowered:
        errors.append("Chart canvases require the Chart.js CDN script.")

    parser = PresentationParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # pragma: no cover - defensive parser boundary
        errors.append(f"HTML parsing failed: {exc}")

    if parser.wrapper_count != 1:
        errors.append(
            "Expected exactly one element with id='presentation-slides-wrapper'; "
            f"found {parser.wrapper_count}."
        )
    if parser.slide_count < 1:
        errors.append("The presentation wrapper must have at least one direct element child.")
    if parser.direct_text:
        errors.append("The presentation wrapper contains non-whitespace text outside slide elements.")

    width_signal = re.search(r"(?:width\s*:\s*1280px|w-\[1280px\])", html, re.I)
    height_signal = re.search(r"(?:height\s*:\s*720px|h-\[720px\])", html, re.I)
    if not width_signal or not height_signal:
        errors.append("Missing a recognizable 1280×720 px slide dimension rule.")

    local_sources = re.findall(
        r"(?:src|href)\s*=\s*['\"](?!https://|data:|#|mailto:|tel:)([^'\"]+)['\"]",
        html,
        re.I,
    )
    if local_sources:
        examples = ", ".join(local_sources[:3])
        errors.append(f"Use absolute HTTPS or data URLs instead of local/relative assets: {examples}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="HTML presentation file")
    args = parser.parse_args()

    try:
        source = args.html.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Could not read {args.html}: {exc}", file=sys.stderr)
        return 2

    errors = validate_html(source)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    parsed = PresentationParser()
    parsed.feed(source)
    print(f"OK: {args.html} contains {parsed.slide_count} slide(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
