"""Pruebas del archivo de entrada directo."""

import importlib.util
import unittest
from pathlib import Path


class EntrypointTests(unittest.TestCase):
    def test_src_main_file_imports_without_starting_app(self):
        path = Path("src/main.py")
        spec = importlib.util.spec_from_file_location("chivatask_main", path)
        module = importlib.util.module_from_spec(spec)

        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        self.assertTrue(callable(module.main))

    def test_composition_root_opens_main_window_maximized(self):
        source = Path("src/app/__init__.py").read_text(encoding="utf-8")

        self.assertIn("window.showMaximized()", source)
        self.assertIn("login.exec_maximized()", source)


if __name__ == "__main__":
    unittest.main()
