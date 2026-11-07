"""Regression tests for bounded, read-only local JSON tools."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = [ROOT / "skills" / skill / "scripts/query.py"
         for skill in ("campus-card-skill", "world-book-skill")]
TOOLS.append(ROOT / "skills/campus-card-skill/scripts/card-audit.py")


class PrivacyTests(unittest.TestCase):
    def run_tool(self, tool, path, *args):
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(tool), str(path), *args],
                              capture_output=True, encoding="utf-8", timeout=10)

    def test_queries_are_read_only_and_do_not_follow_file_references(self):
        for tool in TOOLS[:2]:
            with self.subTest(tool=tool.parent.parent.name), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                private = base / "private.txt"
                private.write_text("synthetic-private-marker", encoding="utf-8")
                book = base / "book.json"
                book.write_text(json.dumps({"entries": {
                    "0": {"uid": 0, "content": "See @1", "comment": "First"},
                    "1": {"uid": 1, "content": "@private.txt", "comment": "Second"}
                }}), encoding="utf-8")
                before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in base.iterdir()}
                for mode in ((), ("--brief",), ("--resolve",), ("--uid", "1"), ("--search", "First")):
                    result = self.run_tool(tool, book, *mode)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn(directory, result.stdout + result.stderr)
                    self.assertNotIn("synthetic-private-marker", result.stdout)
                    data = json.loads(result.stdout)
                    if "worldbook" in data:
                        self.assertEqual(data["worldbook"], "book.json")
                after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in base.iterdir()}
                self.assertEqual(before, after)

    def test_failures_do_not_disclose_paths_or_tracebacks(self):
        for tool in TOOLS:
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input.json"
                for content in (None, b"{broken", b"\xff", b"[" * 2000 + b"]" * 2000):
                    if content is not None:
                        path.write_bytes(content)
                    result = self.run_tool(tool, path)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn(directory, result.stdout + result.stderr)
                    self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_large_input_is_rejected_without_rewrite(self):
        for tool in TOOLS:
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "large.json"
                payload = b" " * (8 * 1024 * 1024 + 1)
                path.write_bytes(payload)
                result = self.run_tool(tool, path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(path.read_bytes(), payload)
                self.assertNotIn(directory, result.stdout + result.stderr)

    def test_production_tools_have_no_execution_network_or_write_calls(self):
        permitted_imports = {"argparse", "json", "os", "sys", "re", "pathlib"}
        forbidden_calls = {"eval", "exec", "compile", "__import__", "system", "popen", "run",
                           "unlink", "remove", "rename", "replace", "write", "write_text", "write_bytes",
                           "mkdir", "makedirs", "rmdir", "rmtree"}
        for tool in TOOLS:
            tree = ast.parse(tool.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(alias.name in permitted_imports for alias in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, permitted_imports)
                elif isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                    self.assertNotIn(name, forbidden_calls)
                    if name == "open":
                        mode = node.args[1] if isinstance(node.func, ast.Name) else node.args[0]
                        self.assertIsInstance(mode, ast.Constant)
                        self.assertIn(mode.value, ("r", "rb"))


if __name__ == "__main__":
    unittest.main()
