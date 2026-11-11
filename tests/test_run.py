"""Exercise Make's run shortcut with a temporary echo program, not real solutions."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RunTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        (self.root / "scripts").mkdir()
        shutil.copyfile(ROOT / "scripts/run_problem.py", self.root / "scripts/run_problem.py")
        (self.root / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.16)\n"
            "project(RunFixture NONE)\nadd_custom_target(problem_1234)\n")
        inputs = self.root / "problems/1234/in"
        inputs.mkdir(parents=True)
        (inputs / "2.txt").write_text("selected input\n")
        for number in range(3, 10):
            (inputs / f"{number}.txt").write_text(f"input {number}\n")
        (inputs / "02.txt").write_text("zero-padded input\n")
        binary = self.root / "build/problems/1234/problem_1234"
        binary.parent.mkdir(parents=True)
        binary.symlink_to(shutil.which("cat"))

    def run_problem(self, case=None, stdin=""):
        command = ["make", "--no-print-directory", "run", "ID=1234"]
        if case is not None:
            command.append("CASE=" + case)
        return subprocess.run(command, cwd=self.root, input=stdin,
                              capture_output=True, text=True)

    def test_no_case_preserves_stdin(self):
        result = self.run_problem(stdin="manual input\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("manual input\n"), result.stdout)

    def test_selected_case_uses_file_not_stdin(self):
        result = self.run_problem("2", stdin="ignore this\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("selected input\n"), result.stdout)
        self.assertNotIn("ignore this", result.stdout)

    def test_zero_padded_case(self):
        result = self.run_problem("02")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("zero-padded input\n"), result.stdout)

    def test_comma_list_runs_in_order(self):
        result = self.run_problem("3,2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(result.stdout.index("=== test input 3 ==="),
                        result.stdout.index("=== test input 2 ==="))
        self.assertIn("input 3", result.stdout)
        self.assertTrue(result.stdout.endswith("selected input\n"))

    def test_inclusive_range_builds_once(self):
        result = self.run_problem("2-9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("=== test input"), 8)
        self.assertEqual(result.stdout.count("cmake --build"), 1)
        self.assertIn("=== test input 9 ===", result.stdout)

    def test_mixed_selection_deduplicates(self):
        result = self.run_problem("2,3-5,3,2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("=== test input"), 4)

    def test_zero_padded_range(self):
        (self.root / "problems/1234/in/03.txt").write_text("padded 3\n")
        result = self.run_problem("02-03")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("zero-padded input", result.stdout)
        self.assertTrue(result.stdout.endswith("padded 3\n"))

    def test_descending_range_is_rejected(self):
        result = self.run_problem("9-2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Descending range", result.stderr)
        self.assertFalse((self.root / "build/CMakeCache.txt").exists())

    def test_missing_case_in_list_fails_before_running(self):
        result = self.run_problem("2,99")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Test input not found", result.stderr)
        self.assertNotIn("selected input", result.stdout)
        self.assertFalse((self.root / "build/CMakeCache.txt").exists())

    def test_missing_case_fails_before_build(self):
        result = self.run_problem("99")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Test input not found", result.stderr)
        self.assertFalse((self.root / "build/CMakeCache.txt").exists())

    def test_invalid_case_fails_before_build(self):
        for case in ("../2", "2,,3", "abc"):
            with self.subTest(case=case):
                result = self.run_problem(case)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Invalid case selection", result.stderr)
                self.assertFalse((self.root / "build/CMakeCache.txt").exists())


class IncrementalBuildTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        (self.root / "scripts").mkdir()
        shutil.copyfile(ROOT / "scripts/run_problem.py", self.root / "scripts/run_problem.py")
        self.cmake = self.root / "CMakeLists.txt"
        self.cmake.write_text(
            'cmake_minimum_required(VERSION 3.16)\nproject(IncrementalFixture CXX)\n'
            'message(STATUS "RUN_FIXTURE_CONFIGURE")\n'
            'add_executable(problem_1234 main.cpp)\n'
            'set_target_properties(problem_1234 PROPERTIES RUNTIME_OUTPUT_DIRECTORY '
            '"${CMAKE_BINARY_DIR}/problems/1234")\n')
        self.source = self.root / "main.cpp"
        self.source.write_text('#include "value.hpp"\nint main() { return VALUE; }\n')
        self.header = self.root / "value.hpp"
        self.header.write_text('#define VALUE 0\n')
        self.binary = self.root / "build/problems/1234/problem_1234"
        self.object = self.root / "build/CMakeFiles/problem_1234.dir/main.cpp.o"
        self.cache = self.root / "build/CMakeCache.txt"

    def make(self, *args):
        result = subprocess.run(["make", "--no-print-directory", *args], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def test_unchanged_run_does_not_configure_compile_or_link(self):
        first = self.make("run", "ID=1234")
        self.assertIn("RUN_FIXTURE_CONFIGURE", first)
        paths = (self.binary, self.object, self.cache)
        timestamps = [path.stat().st_mtime_ns for path in paths]
        second = self.make("run", "ID=1234")
        self.assertNotIn("RUN_FIXTURE_CONFIGURE", second)
        self.assertNotIn("Building CXX", second)
        self.assertNotIn("Linking CXX", second)
        self.assertEqual(timestamps, [path.stat().st_mtime_ns for path in paths])

    def test_source_and_header_changes_rebuild(self):
        self.make("run", "ID=1234")
        for path in (self.source, self.header):
            with self.subTest(path=path.name):
                previous = self.object.stat().st_mtime_ns
                time.sleep(0.02)
                path.write_text(path.read_text() + "\n// changed\n")
                output = self.make("run", "ID=1234")
                self.assertNotIn("RUN_FIXTURE_CONFIGURE", output)
                self.assertGreater(self.object.stat().st_mtime_ns, previous)

    def test_cmake_changes_regenerate_automatically(self):
        self.make("run", "ID=1234")
        time.sleep(0.02)
        self.cmake.write_text(self.cmake.read_text() + "\n# changed configuration\n")
        output = self.make("run", "ID=1234")
        self.assertIn("RUN_FIXTURE_CONFIGURE", output)

    def test_clean_and_distclean_recover(self):
        self.make("run", "ID=1234")
        self.make("clean")
        self.assertFalse(self.binary.exists())
        self.make("run", "ID=1234")
        self.assertTrue(self.binary.is_file())
        self.make("distclean")
        self.assertFalse(self.cache.exists())
        output = self.make("run", "ID=1234")
        self.assertIn("RUN_FIXTURE_CONFIGURE", output)
        self.assertTrue(self.binary.is_file())


if __name__ == "__main__":
    unittest.main()
