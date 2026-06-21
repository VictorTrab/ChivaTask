"""Pruebas de carga de iconos SVG locales."""

import unittest

from PySide6.QtWidgets import QApplication

from PySide6.QtGui import QIcon

from presentation.qt.logo import lockup_path, logo_icon, logo_path
from presentation.qt.registro_iconos import IconRegistry


class IconRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_declared_tabler_icons_load(self):
        registry = IconRegistry()
        for name in registry.ICONS:
            with self.subTest(name=name):
                self.assertFalse(registry.icon(name).isNull())

    def test_brand_icon_loads(self):
        self.assertFalse(logo_icon().isNull())

    def test_brand_svgs_scale_to_common_sizes(self):
        icon = QIcon(logo_path())
        for size in (16, 24, 32, 64):
            with self.subTest(size=size):
                self.assertFalse(icon.pixmap(size, size).isNull())
        self.assertFalse(QIcon(lockup_path()).isNull())


if __name__ == "__main__":
    unittest.main()
