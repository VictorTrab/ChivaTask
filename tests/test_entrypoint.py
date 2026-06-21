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


if __name__ == "__main__":
    unittest.main()
