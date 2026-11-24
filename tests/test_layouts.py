"""Regression coverage for workspace isolation, overflow, settings and recovery."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_engine import FakeHypr, MONITOR, window
from engine import Controller, Journal, geometry, identity
from settings import Settings, ratios


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.hypr = FakeHypr()
        self.now = 10
        self.settings = Settings(self.path / "settings.json")
        self.c = Controller(self.hypr, Journal(self.path / "journal.json"),
                            lambda: self.now, self.settings)

    def tick(self):
        self.now += 2
        self.c.reconcile()

    def switch(self, workspace):
        self.hypr.monitors[0]["activeWorkspace"] = {"id": workspace, "name": str(workspace)}
        self.tick()

    def test_independent_workspace_toggle_and_return(self):
        self.hypr.clients = [window(n, 1 if n < 4 else 2) for n in range(1, 7)]
        self.c.command({"command": "toggle"})
        first = copy.deepcopy(self.hypr.clients[:3])
        self.switch(2)
        self.assertFalse(self.c.status()["current_active"])
        self.c.command({"command": "toggle"})
        self.assertEqual(self.c.workspaces, {1, 2})
        self.assertEqual(self.hypr.clients[:3], first)
        self.c.command({"command": "toggle"})
        self.assertEqual(self.c.workspaces, {1})
        self.assertTrue(all(c["floating"] for c in self.hypr.clients[:3]))
        self.assertFalse(any(c["floating"] for c in self.hypr.clients[3:]))
        self.assertTrue(self.hypr.hotkeys)
        self.switch(1)
        self.assertTrue(self.c.status()["current_active"])
        self.assertEqual(self.hypr.clients[:3], first)

    def test_many_windows_remain_visible_without_workspace_moves(self):
        self.hypr.clients = [window(n) for n in range(1, 11)]
        self.c.activate()
        self.tick()
        self.tick()
        self.assertEqual(self.c.workspaces, {1})
        self.assertFalse(any(call[0] == "move" for call in self.hypr.calls))
        self.assertEqual(len(self.c.records), 10)
        for c in self.hypr.clients:
            x, y = c["at"]
            w, h = c["size"]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 26)
            self.assertLessEqual(x + w, 3440)
            self.assertLessEqual(y + h, 1440)
            self.assertGreater(h, 0)
            self.assertEqual(c["workspace"]["id"], 1)
        for a in self.hypr.clients:
            for b in self.hypr.clients:
                if a is b:
                    continue
                self.assertTrue(a["at"][0] + a["size"][0] <= b["at"][0]
                                or b["at"][0] + b["size"][0] <= a["at"][0]
                                or a["at"][1] + a["size"][1] <= b["at"][1]
                                or b["at"][1] + b["size"][1] <= a["at"][1])

    def test_closing_stack_member_expands_remaining_window(self):
        self.hypr.clients = [window(n) for n in range(1, 5)]
        self.c.activate()
        self.tick()
        center = self.hypr.clients[0]
        self.assertLess(center["size"][1], 1392)
        self.hypr.clients.pop()
        self.tick()
        self.tick()
        self.assertEqual(center["size"][1], 1392)

    def test_hidden_workspace_geometry_does_not_release_windows(self):
        self.hypr.clients = [window(1)]
        self.c.activate()
        self.switch(2)
        c = self.hypr.clients[0]
        c["at"] = [-9000, -9000]
        for _ in range(10):
            self.tick()
        self.assertIn(identity(c), self.c.records)
        self.assertTrue(c["floating"])
        self.switch(1)
        self.assertEqual(c["at"], [1041, 37])

    def test_ratios_persist_per_workspace_and_apply_immediately(self):
        self.hypr.clients = [window(1), window(2, 2)]
        self.c.activate()
        self.c.command({"command": "ratios", "value": [25, 50, 25]})
        self.tick()
        # 3394 usable pixels; rounded 25% side columns are 848 pixels each.
        self.assertEqual(self.hypr.clients[0]["size"][0], 1698)
        self.switch(2)
        self.c.activate()
        self.assertEqual(self.hypr.clients[1]["size"][0], 1358)
        restored = Settings(self.settings.path)
        self.assertEqual(restored.profile(1)["ratios"], [25, 50, 25])
        self.assertEqual(restored.profile(2)["ratios"], [30, 40, 30])
        before = self.settings.path.read_text()
        with self.assertRaises(ValueError):
            self.c.command({"command": "ratios", "value": [20, 20, 20]})
        self.assertEqual(self.settings.path.read_text(), before)

    def test_auto_visits_and_manual_opt_out(self):
        self.hypr.clients = [window(1), window(2, 2), window(3, 3)]
        self.c.command({"command": "auto", "value": True})
        self.assertEqual(self.c.workspaces, {1})
        self.switch(2)
        self.assertEqual(self.c.workspaces, {1, 2})
        self.c.command({"command": "toggle"})
        self.switch(1)
        self.switch(2)
        self.assertEqual(self.c.workspaces, {1})
        self.switch(3)
        self.assertEqual(self.c.workspaces, {1, 3})
        self.c.command({"command": "deactivate"})
        self.switch(1)
        self.assertFalse(self.c.active)
        self.assertFalse(self.c.auto_running)

    def test_recovery_restores_all_workspaces_and_stacks(self):
        self.hypr.clients = [window(n, 1 if n <= 4 else 2) for n in range(1, 9)]
        self.c.activate()
        self.switch(2)
        self.c.activate()
        self.assertEqual(len(self.c.journal.load()), 8)
        Controller(self.hypr, self.c.journal)
        self.assertFalse(any(c["floating"] for c in self.hypr.clients))
        self.assertEqual(self.c.journal.load(), [])

    def test_move_between_managed_workspaces_keeps_ownership(self):
        self.hypr.clients = [window(n) for n in range(1, 5)] + [window(9, 2)]
        self.c.activate()
        self.switch(2)
        self.c.activate()
        moved = self.hypr.clients[0]
        moved["workspace"] = {"id": 2, "name": "2"}
        self.tick()
        self.assertEqual(self.c.records[identity(moved)]["workspace"], 2)
        self.assertTrue(moved["floating"])

    def test_stack_hotkey_swaps_and_preserves_all_windows(self):
        self.hypr.clients = [window(n) for n in range(1, 7)]
        self.c.activate()
        self.tick()
        c = self.hypr.clients[0]
        self.c.move_slot("l", c["address"], c["stableId"])
        self.tick()
        self.tick()
        self.assertEqual(self.c.records[identity(c)]["slot"], "left")
        self.assertEqual(len(self.c.records), 6)
        self.assertEqual(set(c["workspace"]["id"] for c in self.hypr.clients), {1})

    def test_slow_window_can_settle_before_release(self):
        self.hypr.clients = [window(1)]
        self.hypr.stubborn = True
        self.c.activate()
        self.tick()
        self.tick()
        self.hypr.stubborn = False
        self.tick()
        self.tick()
        self.assertEqual(len(self.c.records), 1)
        self.assertTrue(self.hypr.clients[0]["floating"])

    def test_failed_restore_keeps_workspace_and_journal(self):
        self.hypr.clients = [window(1)]
        self.c.activate()
        self.hypr.fail = True
        with self.assertRaises(RuntimeError):
            self.c.disable_workspace(1)
        self.assertEqual(self.c.workspaces, {1})
        self.assertTrue(self.c.journal.load())
        self.hypr.fail = False
        self.c.disable_workspace(1)
        self.assertFalse(self.c.active)
        self.assertEqual(self.c.journal.load(), [])

    def test_two_monitors_keep_independent_geometry_and_disconnect_cleanup(self):
        second = dict(copy.deepcopy(MONITOR), id=1, name="HDMI-A-1", x=3440,
                      width=2560, activeWorkspace={"id": 2, "name": "2"})
        self.hypr.monitors.append(second)
        self.hypr.clients = [window(1), dict(window(2, 2), monitor=1)]
        self.c.activate()
        self.hypr.monitors[0]["focused"] = False
        self.c.activate()
        self.tick()
        self.assertLess(self.hypr.clients[0]["at"][0], 3440)
        self.assertGreater(self.hypr.clients[1]["at"][0], 3440)
        self.assertEqual(self.c.workspaces, {1, 2})
        self.hypr.monitors.pop()
        # A disconnected monitor's workspace may temporarily retain its name.
        self.hypr.extra_workspaces = [{"id": 2, "monitor": "HDMI-A-1"}]
        self.tick()
        # Suspended, not released: its windows are left alone until it returns.
        self.assertEqual(self.c.workspaces, {1, 2})
        self.assertEqual(self.c.suspended, {2})
        self.assertTrue(self.hypr.clients[0]["floating"])
        self.assertTrue(self.hypr.clients[1]["floating"])
        self.hypr.monitors.append(second)
        self.hypr.extra_workspaces = []
        self.tick()
        self.assertEqual(self.c.suspended, set())
        self.assertGreater(self.hypr.clients[1]["at"][0], 3440)

    def restart(self):
        """Simulate a shell reload or login: shutdown, then a fresh controller."""
        self.c.deactivate()
        self.settings = Settings(self.path / "settings.json")
        self.c = Controller(self.hypr, Journal(self.path / "journal.json"),
                            lambda: self.now, self.settings)

    def test_enabled_workspaces_survive_restart(self):
        self.hypr.clients = [window(1), window(2), window(3, 3)]
        self.c.command({"command": "toggle"})
        self.switch(3)
        self.c.command({"command": "toggle"})
        self.assertEqual(self.settings.enabled, {1, 3})
        self.restart()
        self.assertFalse(any(c["floating"] for c in self.hypr.clients))
        self.hypr.calls.clear()
        self.tick()
        self.assertEqual(self.c.workspaces, {1, 3})
        self.assertTrue(all(c["floating"] for c in self.hypr.clients))
        # Background restore of workspace 1 must not steal focus from 3.
        self.assertEqual([c for c in self.hypr.calls if c[0] == "focus"], [("focus", "0x3")])
        self.assertEqual(self.hypr.clients[0]["size"][0], self.c.layouts[1]["center"][2])

    def test_remembered_workspace_waits_until_it_exists(self):
        self.hypr.clients = [window(1)]
        self.c.command({"command": "toggle"})
        self.switch(4)
        self.c.command({"command": "toggle"})  # Empty workspace 4.
        self.restart()
        self.switch(1)
        self.assertEqual(self.c.workspaces, {1})
        self.switch(4)
        self.assertEqual(self.c.workspaces, {1, 4})

    def test_toggle_off_and_deactivate_forget_workspaces(self):
        self.hypr.clients = [window(1), window(2, 2)]
        self.c.command({"command": "toggle"})
        self.switch(2)
        self.c.command({"command": "toggle"})
        self.c.command({"command": "toggle"})
        self.assertEqual(self.settings.enabled, {1})
        self.restart()
        self.tick()
        self.assertEqual(self.c.workspaces, {1})
        self.c.command({"command": "deactivate"})
        self.assertEqual(self.settings.enabled, set())
        self.restart()
        self.tick()
        self.assertFalse(self.c.active)

    def test_activation_does_not_lose_pending_open_on_another_workspace(self):
        self.hypr.clients = [window(1)]
        self.c.activate()
        self.hypr.clients.append(window(2))
        self.hypr.monitors[0]["activeWorkspace"] = {"id": 2, "name": "2"}
        self.c.activate()
        self.tick()
        self.assertIn(identity(self.hypr.clients[1]), self.c.records)


class SettingsTests(unittest.TestCase):
    def test_invalid_ratios(self):
        for value in (None, "30,40,30", [30, 70], [0, 0, 0], [1, 49, 50], [-10, 60, 50],
                      [True, 49, 50], [float("nan"), 50, 50], [float("inf"), 0, 0]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ratios(value)

    def test_asymmetric_and_fractional_ratios_fill_width(self):
        g = geometry(MONITOR, [10]*4, [5]*4, 1, [20.5, 49, 30.5])
        self.assertLess(g["left"][2], g["right"][2])
        self.assertEqual(g["right"][0] + g["right"][2], 3429)

    def test_malformed_settings_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            for value in ({"auto": "yes"}, {"workspaces": {"1": {"overflow": "close"}}},
                          {"workspaces": {"-1": {}}}, {"enabled": "1"},
                          {"enabled": [0]}, {"enabled": [True]}, {"enabled": [1.5]}):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    Settings(path)
