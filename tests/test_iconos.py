"""Pruebas de carga de iconos SVG locales."""

import unittest

from PySide6.QtWidgets import QApplication

from PySide6.QtGui import QIcon

from presentation.qt.logo import lockup_path, logo_icon, logo_path
from presentation.qt.registro_iconos import IconRegistry


def _contrast_ratio(foreground: str, background: str) -> float:
    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: str) -> float:
    red, green, blue = (
        int(color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    )
    return 0.2126 * _linear(red) + 0.7152 * _linear(green) + 0.0722 * _linear(blue)


def _linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


class IconRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_declared_tabler_icons_load(self):
        registry = IconRegistry()
        self.assertIn("moon", registry.ICONS)
        self.assertIn("sun", registry.ICONS)
        for name in registry.ICONS:
            with self.subTest(name=name):
                self.assertFalse(registry.icon(name).isNull())

    def test_tabler_icons_have_contrast_tones(self):
        registry = IconRegistry()
        dark_icon = registry.icon("search", "dark").pixmap(24, 24).toImage()
        light_icon = registry.icon("search", "light").pixmap(24, 24).toImage()

        dark_pixels = []
        light_pixels = []
        for x in range(24):
            for y in range(24):
                dark_color = dark_icon.pixelColor(x, y)
                light_color = light_icon.pixelColor(x, y)
                if dark_color.alpha() > 0:
                    dark_pixels.append(dark_color.lightness())
                if light_color.alpha() > 0:
                    light_pixels.append(light_color.lightness())

        self.assertTrue(dark_pixels)
        self.assertTrue(light_pixels)
        self.assertLess(sum(dark_pixels) / len(dark_pixels), 110)
        self.assertGreater(sum(light_pixels) / len(light_pixels), 220)

    def test_semantic_icon_tones_are_registered(self):
        registry = IconRegistry()
        for tone in ("muted", "brand", "warning", "danger", "info"):
            with self.subTest(tone=tone):
                self.assertFalse(registry.icon("bell", tone).isNull())

    def test_semantic_icon_tones_keep_graphic_contrast(self):
        backgrounds = ("#FFFFFF", "#182331")
        for tone in ("muted", "brand", "warning", "danger", "info"):
            for background in backgrounds:
                with self.subTest(tone=tone, background=background):
                    self.assertGreaterEqual(
                        _contrast_ratio(IconRegistry.TONES[tone], background),
                        3.0,
                    )

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
