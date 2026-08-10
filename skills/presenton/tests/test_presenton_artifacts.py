from __future__ import annotations

import argparse
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import presenton_artifacts  # noqa: E402


class PresentonResponseMessageTests(unittest.TestCase):
    def test_search_reads_wrapped_designs_and_shows_message(self) -> None:
        response = {
            "designs": [
                {
                    "id": 7,
                    "title": "Editorial Board Review",
                    "description": "Restrained navy and cream",
                }
            ],
            "message": "Search guidance for the user",
        }
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch.object(presenton_artifacts, "request_json", return_value=response),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = presenton_artifacts.command_search(argparse.Namespace(query="review"))

        self.assertEqual(result, 0)
        self.assertIn("Editorial Board Review (id=7)", stdout.getvalue())
        self.assertIn("API message: Search guidance for the user", stderr.getvalue())

    def test_export_shows_message_and_keeps_url_as_only_stdout_value(self) -> None:
        with tempfile.TemporaryDirectory(prefix="presenton-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            (temp_dir / presenton_artifacts.TEMP_MARKER_NAME).write_text(
                presenton_artifacts.TEMP_MARKER_CONTENT,
                encoding="utf-8",
            )
            html_path = temp_dir / "presentation.html"
            html_path.write_text("<html></html>", encoding="utf-8")
            response = {
                "url": "https://api.example.test/s/export",
                "message": "Export guidance for the user",
            }
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch.object(presenton_artifacts, "validate_html", return_value=[]),
                patch.object(presenton_artifacts, "request_json", return_value=response),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                result = presenton_artifacts.command_export(
                    argparse.Namespace(
                        html=html_path,
                        format="pptx",
                        title=None,
                        design_id=None,
                    )
                )

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "https://api.example.test/s/export\n")
        self.assertIn("API message: Export guidance for the user", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
