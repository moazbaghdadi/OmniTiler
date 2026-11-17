import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine import Controller, Journal
from settings import Settings
from test_engine import FakeHypr, window


class PresetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        self.settings = Settings(self.path)
        self.hypr = FakeHypr([window(1), window(2, 2)])
        self.c = Controller(self.hypr, Journal(self.path.with_name("journal.json")), settings=self.settings)

    def test_upgrade_old_settings_and_preserve_new_presets_on_other_writes(self):
        self.path.write_text(json.dumps({"auto": True, "workspaces": {
            "2": {"ratios": [20, 45, 35], "overflow": "workspace"}}}))
        old = Settings(self.path)
        self.assertEqual(len(old.presets), 2)
        old.save_preset(None, [20, 60, 20], 1)
        old.set_auto(False)
        old.update(1, overflow="workspace")
        loaded = Settings(self.path)
        self.assertEqual(len(loaded.presets), 3)
        self.assertEqual(loaded.profile(2), {"ratios": [20, 45, 35], "overflow": "workspace"})

    def test_add_edit_and_restart_preserves_ids(self):
        self.settings.save_preset(None, [20, 60, 20], 1)
        key = self.settings.presets[-1]["id"]
        self.settings.save_preset(key, [20, 45, 35], 1)
        loaded = Settings(self.path)
        self.assertEqual(len(loaded.presets), 3)
        self.assertEqual(loaded.preset(key)["ratios"], [20, 45, 35])
        self.assertEqual(loaded.profile(1)["ratios"], [20, 45, 35])

    def test_edit_affects_only_target_workspace(self):
        self.settings.update(2, ratios=[30, 40, 30])
        self.c.command({"command": "save_preset", "value": {
            "id": "balanced", "ratios": [20, 60, 20], "workspace": 1}})
        self.assertEqual(self.settings.profile(1)["ratios"], [20, 60, 20])
        self.assertEqual(self.settings.profile(2)["ratios"], [30, 40, 30])

    def test_apply_uses_captured_workspace_even_after_focus_switch(self):
        self.c.command({"command": "apply_preset", "value": {"id": "wide-center", "workspace": 2}})
        self.assertEqual(self.settings.profile(2)["ratios"], [25, 50, 25])
        self.assertEqual(self.settings.profile(1)["ratios"], [30, 40, 30])
        self.assertEqual(self.c.status()["profiles"]["2"]["ratios"], [25, 50, 25])
        self.assertFalse(self.c.active)

    def test_invalid_input_does_not_change_settings(self):
        self.settings.set_auto(False)
        before = self.path.read_text()
        for value in ({"id": "missing", "workspace": 1}, {"id": "balanced", "workspace": -1},
                      {"id": "balanced", "workspace": True}, {"id": "balanced", "workspace": "1"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.c.command({"command": "apply_preset", "value": value})
        with self.assertRaises(ValueError):
            self.settings.save_preset("balanced", [10, 10, 10], 1)
        self.assertEqual(self.path.read_text(), before)

    def test_failed_write_leaves_presets_and_workspace_unchanged(self):
        before = json.dumps(self.settings.presets)
        with patch.object(self.settings, "save", side_effect=OSError("Disk full")):
            with self.assertRaises(OSError):
                self.settings.save_preset("balanced", [20, 60, 20], 1)
        self.assertEqual(json.dumps(self.settings.presets), before)
        self.assertEqual(self.settings.profiles, {})

    def test_preset_limit_and_persistent_validation(self):
        for _ in range(14):
            self.settings.save_preset(None, [30, 40, 30], 1)
        with self.assertRaises(ValueError):
            self.settings.save_preset(None, [30, 40, 30], 1)
        self.assertEqual(len(self.settings.presets), 16)
        for value in ([], [{"id": "<img>", "ratios": [30, 40, 30]}],
                      [{"id": "a", "ratios": [30, 40, 30]}] * 2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Settings.validate_presets(value)

    def test_cycle_includes_custom_presets(self):
        self.settings.save_preset(None, [20, 60, 20], 1)
        self.settings.update(1, ratios=[25, 50, 25])
        self.c.command({"command": "preset"})
        self.assertEqual(self.settings.profile(1)["ratios"], [20, 60, 20])
