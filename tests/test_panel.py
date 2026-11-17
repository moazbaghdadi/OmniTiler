"""Actual QML controls tested offscreen; no installed plugin or desktop changes."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which("qs") and Path("/usr/share/omarchy/shell").exists(),
                     "QML integration checks require Omarchy and Quickshell")
class PanelTests(unittest.TestCase):
    def test_preset_panel_mouse_keyboard_and_validation(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "qs").symlink_to("/usr/share/omarchy/shell")
            for module in ("Commons", "Ui"):
                (path / module).symlink_to(Path("/usr/share/omarchy/shell") / module)
            harness = path / "shell.qml"
            harness.write_text((root / "tests/qml/presets.qml").read_text().replace(
                'import "../.." as Plugin', f'import "{root.as_uri()}" as Plugin'))
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QPA_PLATFORMTHEME="basic",
                               QML_IMPORT_PATH=directory, XDG_RUNTIME_DIR=directory)
            result = subprocess.run(["qs", "-p", str(harness), "--no-color"],
                                    env=environment, capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("OMNITILER_PANEL_TESTS_PASSED", output)
            self.assertNotIn("OMNITILER_PANEL_TEST_FAILED", output)
            self.assertNotIn("ReferenceError", output)
            self.assertNotIn("TypeError", output)
