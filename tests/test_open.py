"""Editor shortcuts are tested without launching any real editors."""

import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import open_problem


class OpenProblemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(open_problem, "ROOT", self.root))
        stack.enter_context(patch.dict(os.environ, {}, clear=True))

    def test_default_and_standard_editor_variables(self):
        self.assertEqual(open_problem.editor_command(), ["code"])
        with patch.dict(os.environ, {"EDITOR": "vim -n"}):
            self.assertEqual(open_problem.editor_command(), ["vim", "-n"])
            with patch.dict(os.environ, {"VISUAL": "nvim"}):
                self.assertEqual(open_problem.editor_command(), ["nvim"])

    def test_dotenv_environment_and_explicit_precedence(self):
        (self.root / ".env").write_text('CSES_EDITOR="code --wait"\n')
        with patch.dict(os.environ, {"EDITOR": "vim"}):
            self.assertEqual(open_problem.editor_command(), ["code", "--wait"])
            with patch.dict(os.environ, {"CSES_EDITOR": "nvim"}):
                self.assertEqual(open_problem.editor_command(), ["nvim"])
                self.assertEqual(open_problem.editor_command("vim -n"), ["vim", "-n"])

    def test_quoted_executable_and_no_shell_expansion(self):
        self.assertEqual(open_problem.editor_command('"/path with spaces/editor" --wait'),
                         ["/path with spaces/editor", "--wait"])
        self.assertEqual(open_problem.editor_command("code $(touch nope)"),
                         ["code", "$(touch", "nope)"])
        self.assertFalse((self.root / "nope").exists())

    def test_opens_only_the_solution(self):
        source = self.root / "problems/1069/main.cpp"
        source.parent.mkdir(parents=True)
        source.write_text("int main() {}\n")
        with patch("sys.argv", ["open_problem.py", "1069", "--editor", "vim -n"]), \
                patch.object(open_problem.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertEqual(open_problem.main(), 0)
            run.assert_called_once_with(["vim", "-n", str(source)], cwd=self.root)

    def test_missing_problem_does_not_launch_editor(self):
        with patch("sys.argv", ["open_problem.py", "1069"]), \
                patch.object(open_problem.subprocess, "run") as run, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(open_problem.main(), 1)
            run.assert_not_called()

    def test_invalid_id(self):
        with patch("sys.argv", ["open_problem.py", "../1069"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            open_problem.main()

    def test_missing_editor_is_reported(self):
        source = self.root / "problems/1069/main.cpp"
        source.parent.mkdir(parents=True)
        source.write_text("")
        with patch("sys.argv", ["open_problem.py", "1069"]), \
                patch.object(open_problem.subprocess, "run", side_effect=FileNotFoundError), \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(open_problem.main(), 1)
            self.assertIn("Editor executable not found", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
