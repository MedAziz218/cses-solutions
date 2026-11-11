"""Offline tooling checks. Run with just check or make check."""

import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import add_problem
import cses_config
import init as init_project

ROOT = Path(__file__).resolve().parents[1]


def archive(files):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as output:
        for name, content in files.items():
            output.writestr(name, content)
    return data.getvalue()


class CredentialTests(unittest.TestCase):
    def test_dotenv_and_precedence(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            root = Path(temp)
            (root / ".env").write_text("# Local config\nCSES_USERNAME=local-user\n"
                                       "CSES_PASSWORD='literal # $() = value'\n")
            self.assertEqual(cses_config.get_credentials(root=root),
                             ("local-user", "literal # $() = value"))
            with patch.dict(os.environ, {"CSES_USERNAME": "env-user", "CSES_PASSWORD": "env-pass"}):
                self.assertEqual(cses_config.get_credentials(root=root), ("env-user", "env-pass"))
                self.assertEqual(cses_config.get_credentials("cli-user", "cli-pass", root=root),
                                 ("cli-user", "cli-pass"))

    def test_missing_values_prompt(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True), \
                patch("builtins.input", return_value="prompt-user"), \
                patch.object(cses_config.getpass, "getpass", return_value="prompt-pass"):
            self.assertEqual(cses_config.get_credentials(root=Path(temp)),
                             ("prompt-user", "prompt-pass"))

    def test_malformed_dotenv_does_not_expose_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("CSES_PASSWORD='private-value\n")
            with self.assertRaises(ValueError) as error:
                cses_config.read_dotenv(root)
            self.assertNotIn("private-value", str(error.exception))


class AddProblemTests(unittest.TestCase):
    def test_statement(self):
        parser = add_problem.StatementParser()
        parser.feed('<title>CSES - Example</title><div class="md"><h1>Input</h1>'
                    '<p>Read <span class="math math-inline">n</span>.</p>'
                    '<pre>  first\n second\n</pre></div><div>Navigation</div>')
        text = parser.markdown("1234")
        self.assertIn("# Example", text)
        self.assertIn("## Input", text)
        self.assertIn("$n$", text)
        self.assertIn("```text\n  first\n second\n```", text)
        self.assertNotIn("Navigation", text)

    def test_missing_statement(self):
        with self.assertRaises(ValueError):
            add_problem.StatementParser().markdown("1234")

    def test_invalid_archives(self):
        for files in ({"../1.in": "x"}, {"1.in": "x"}, {}):
            with self.subTest(files=files), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):
                    add_problem.prepare_problem(Path(temp), "1234", archive(files))
                self.assertEqual(list(Path(temp).iterdir()), [])

    def test_add_and_protect_existing_problem(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "problems").mkdir()
            registry = root / "problems/CMakeLists.txt"
            registry.write_text("# Problems\n")
            data = archive({"1.in": "3\n", "1.out": "answer\n"})
            with patch.object(add_problem, "ROOT", root), \
                    patch.object(add_problem, "download_tests", return_value=data) as download, \
                    patch.object(add_problem, "download_statement", return_value="# Example\n"), \
                    patch("sys.argv", ["add_problem.py", "1234", "dummy", "dummy"]), \
                    contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(add_problem.main(), 0)
                folder = root / "problems/1234"
                self.assertEqual((folder / "main.cpp").read_text(), add_problem.STARTER)
                self.assertEqual((folder / "statement.md").read_text(), "# Example\n")
                self.assertEqual((folder / "in/1.txt").read_text(), "3\n")
                self.assertEqual((folder / "out/1.out").read_text(), "answer\n")
                self.assertEqual(registry.read_text(), "# Problems\n")
                with self.assertRaises(SystemExit):
                    add_problem.main()
                self.assertEqual(download.call_count, 1)

    def test_restore_tests_preserves_sources_and_existing_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "1234"
            folder.mkdir()
            (folder / "main.cpp").write_text("my solution")
            data = archive({"1.in": "3\\n", "1.out": "answer\\n"})
            self.assertFalse(add_problem.has_tests(folder))
            self.assertEqual(add_problem.restore_tests(folder, data), 1)
            self.assertTrue(add_problem.has_tests(folder))
            self.assertEqual(add_problem.restore_tests(folder, data), 1)
            self.assertEqual((folder / "main.cpp").read_text(), "my solution")
            self.assertFalse((folder / "statement.md").exists())
            (folder / "in/1.txt").write_text("custom input")
            with self.assertRaises(ValueError):
                add_problem.restore_tests(folder, data)
            self.assertEqual((folder / "in/1.txt").read_text(), "custom input")

    def test_starter_compiles(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "main.cpp"
            source.write_text(add_problem.STARTER)
            result = subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra",
                                     "-pedantic", "-fsyntax-only", str(source)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


class InitTests(unittest.TestCase):
    def test_init_restores_missing_tests_and_skips_on_repeat(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "problems/1234"
            folder.mkdir(parents=True)
            (folder / "main.cpp").write_text("my solution")
            data = archive({"1.in": "3\\n", "1.out": "answer\\n"})
            with patch.object(add_problem, "ROOT", root), \
                    patch.object(add_problem, "download_tests", return_value=data) as download, \
                    patch.object(init_project, "get_credentials", return_value=("dummy", "dummy")) as password, \
                    patch.object(init_project.subprocess, "run") as configure, \
                    patch("sys.argv", ["init.py", "dummy"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(init_project.main(), 0)
                self.assertEqual(init_project.main(), 0)
                self.assertEqual(download.call_count, 1)
                self.assertEqual(password.call_count, 1)
                self.assertEqual(configure.call_count, 2)
                self.assertEqual((folder / "main.cpp").read_text(), "my solution")

    def test_empty_repo_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(add_problem, "ROOT", Path(temp)), \
                patch.object(init_project, "get_credentials") as password, \
                patch.object(init_project.subprocess, "run") as configure, \
                patch("sys.argv", ["init.py"]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(init_project.main(), 0)
            password.assert_not_called()
            configure.assert_called_once()

    def test_missing_dependencies(self):
        with patch.object(init_project.shutil, "which", return_value=None), \
                patch("sys.argv", ["init.py"]), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(init_project.main(), 1)


class TestRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "in").mkdir()
        (self.root / "out").mkdir()
        for case in ("1", "3", "01"):
            (self.root / f"in/{case}.txt").write_text(case + "\n")
            (self.root / f"out/{case}.out").write_text(case + " \n")

    def run_cases(self, selection=None, program=None):
        env = os.environ.copy()
        env.pop("CSES_TEST_CASES", None)
        if selection is not None:
            env["CSES_TEST_CASES"] = selection
        result = subprocess.run([
            "cmake", f"-DPROG={program or shutil.which('cat')}",
            f"-DTEST_DIR={self.root}", f"-DBINARY_DIR={self.root}",
            "-P", str(ROOT / "cmake/test_runner.cmake"),
        ], env=env, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def test_all_and_selected_cases(self):
        for selection, count in ((None, 3), ("3", 1), ("1,3", 2),
                                 ("01.txt", 1), ("1,1", 1)):
            with self.subTest(selection=selection):
                status, text = self.run_cases(selection)
                self.assertEqual(status, 0, text)
                self.assertIn(f"{count} passed, 0 failed out of {count} tests", text)

    def test_invalid_cases(self):
        for selection in ("99", "../1", "1,,3"):
            with self.subTest(selection=selection):
                status, _ = self.run_cases(selection)
                self.assertNotEqual(status, 0)

    def test_wrong_answer(self):
        (self.root / "out/1.out").write_text("wrong\n")
        status, text = self.run_cases("1")
        self.assertNotEqual(status, 0)
        self.assertIn("FAIL: 1.txt", text)

    def test_missing_expected_output(self):
        (self.root / "out/1.out").unlink()
        status, _ = self.run_cases("1")
        self.assertNotEqual(status, 0)

    def test_missing_tests_fail_with_init_instructions(self):
        for path in (self.root / "in").iterdir():
            path.unlink()
        status, text = self.run_cases()
        self.assertNotEqual(status, 0)
        self.assertIn("init", text)

    def test_crash(self):
        status, text = self.run_cases("1", shutil.which("false"))
        self.assertNotEqual(status, 0)
        self.assertIn("crash: 1.txt", text)


if __name__ == "__main__":
    unittest.main()
