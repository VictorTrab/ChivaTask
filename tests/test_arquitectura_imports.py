"""Verifica que dominio y aplicacion no dependan de UI o adapters."""

import ast
import pathlib
import unittest


FORBIDDEN = ("PySide6", "requests", "sqlite3", "keyring", "infrastructure", "presentation")


class ArchitectureImportsTests(unittest.TestCase):
    def test_domain_and_application_keep_clean_imports(self):
        root = pathlib.Path("src")
        files = list((root / "domain").glob("*.py")) + list((root / "application").glob("*.py"))
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            for module in imports:
                with self.subTest(path=str(path), module=module):
                    self.assertFalse(any(module.startswith(forbidden) for forbidden in FORBIDDEN))


if __name__ == "__main__":
    unittest.main()

