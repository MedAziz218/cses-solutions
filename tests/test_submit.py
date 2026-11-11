"""Submission regression tests. All network calls and actual uploads are mocked."""

import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

import add_problem
import submit

FORM = '''<form action="/course/send.php" method="post" enctype="multipart/form-data">
<input type="hidden" name="csrf_token" value="dummy-token">
<input type="hidden" name="task" value="1068">
<input type="hidden" name="type" value="course">
<input type="hidden" name="target" value="problemset">
<input type="file" name="file">
<select name="lang"><option value="C++">C++</select>
<script>var options = {"C++":["C++17","C++20"]};</script></form>'''
RESULT = "https://cses.fi/problemset/result/12345/"


class SubmitTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        folder = root / "problems/1068"
        folder.mkdir(parents=True)
        self.source = folder / "main.cpp"
        self.source.write_text("int main() {}\n")
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(submit, "ROOT", root))
        stack.enter_context(patch("sys.argv", ["submit.py", "1068"]))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.tests = stack.enter_context(patch.object(submit.subprocess, "run"))
        self.credentials = stack.enter_context(patch.object(submit, "get_credentials", return_value=("dummy", "dummy")))
        self.session = stack.enter_context(patch.object(add_problem, "authenticated_session"))
        self.session.return_value.open.return_value.__enter__.return_value.read.return_value = FORM.encode()
        self.upload = stack.enter_context(patch.object(submit, "upload", return_value=RESULT))

    def test_confirmation_defaults_to_no(self):
        for answer in ("", "n", "no", "anything"):
            with self.subTest(answer=answer), patch("builtins.input", return_value=answer):
                self.assertEqual(submit.main(), 0)
        self.credentials.assert_not_called()
        self.session.assert_not_called()
        self.upload.assert_not_called()

    def test_eof_cancels(self):
        with patch("builtins.input", side_effect=EOFError):
            self.assertEqual(submit.main(), 1)
        self.upload.assert_not_called()
        self.session.assert_not_called()

    def test_explicit_confirmation_uploads_once(self):
        for answer in ("y", "YES"):
            self.upload.reset_mock()
            with patch("builtins.input", return_value=answer):
                self.assertEqual(submit.main(), 0)
            self.upload.assert_called_once()
            self.assertEqual(self.upload.call_args.args[-1], self.source.read_bytes())
            self.assertEqual(self.upload.call_args.args[-2]["option"], "C++17")

    def test_failed_local_tests_prevent_submission(self):
        self.tests.side_effect = subprocess.CalledProcessError(1, "make")
        with patch("builtins.input") as confirm:
            self.assertEqual(submit.main(), 1)
        confirm.assert_not_called()
        self.session.assert_not_called()
        self.upload.assert_not_called()

    def test_changed_source_prevents_submission(self):
        self.tests.side_effect = lambda *args, **kwargs: self.source.write_text("changed")
        with patch("builtins.input") as confirm:
            self.assertEqual(submit.main(), 1)
        confirm.assert_not_called()
        self.upload.assert_not_called()

    def test_always_runs_all_cases(self):
        with patch.dict("os.environ", {"CSES_TEST_CASES": "3"}), patch("builtins.input", return_value=""):
            submit.main()
        args, kwargs = self.tests.call_args
        self.assertIn("CASE=", args[0])
        self.assertNotIn("CSES_TEST_CASES", kwargs["env"])

    def test_changed_form_stops_upload(self):
        self.session.return_value.open.return_value.__enter__.return_value.read.return_value = b"Login required"
        with patch("builtins.input", return_value="yes"):
            self.assertEqual(submit.main(), 1)
        self.upload.assert_not_called()


class SubmissionProtocolTests(unittest.TestCase):
    def test_parse_realistic_form(self):
        url, fields = submit.submission_form(FORM, "1068")
        self.assertEqual(url, "https://cses.fi/course/send.php")
        self.assertEqual(fields["task"], "1068")
        self.assertEqual(fields["csrf_token"], "dummy-token")
        self.assertEqual(fields["lang"], "C++")
        self.assertEqual(fields["option"], "C++17")

    def test_unsafe_or_mismatched_form(self):
        for page in (FORM.replace('/course/send.php', 'https://example.org/upload'),
                     FORM.replace('value="1068"', 'value="1083"'),
                     FORM.replace('"C++17"', '"C++98"')):
            with self.subTest(page=page), self.assertRaises(ValueError):
                submit.submission_form(page, "1068")

    def test_multipart_contains_source_and_fields(self):
        source = b'#include <iostream>\nint main() {}\n'
        body, content_type = submit.multipart({"task": "1068"}, source)
        boundary = content_type.split("boundary=")[1]
        self.assertIn(source, body)
        self.assertIn(b'name="task"\r\n\r\n1068\r\n', body)
        self.assertIn(b'filename="main.cpp"', body)
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))

    def test_upload_result_and_no_retry_on_rate_limit(self):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.geturl.return_value = RESULT
        self.assertEqual(submit.upload(opener, "https://cses.fi/course/send.php", {}, b"code"), RESULT)
        opener.open.assert_called_once()
        opener.reset_mock()
        opener.open.side_effect = urllib.error.HTTPError("https://cses.fi", 429, "Too Many Requests", {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            submit.upload(opener, "https://cses.fi/course/send.php", {}, b"code")
        opener.open.assert_called_once()

    def test_unknown_upload_response_is_not_success(self):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.geturl.return_value = "https://cses.fi/login"
        with self.assertRaises(ValueError):
            submit.upload(opener, "https://cses.fi/course/send.php", {}, b"code")
        opener.open.assert_called_once()

    def test_shared_login_and_download(self):
        response = MagicMock()
        response.__enter__.return_value.read.side_effect = [
            b'<input name="csrf_token" value="login-token">', b'<a href="/logout">Log out</a>',
            b'<input name="csrf_token" value="download-token">', b'zip bytes',
        ]
        opener = MagicMock()
        opener.open.return_value = response
        with patch.object(add_problem.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(add_problem.download_tests("1068", "dummy", "dummy"), b"zip bytes")
        self.assertEqual(opener.open.call_count, 4)


if __name__ == "__main__":
    unittest.main()
