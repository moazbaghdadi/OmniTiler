"""A zero ratio removes a column, its gaps and its allocation slot."""
from pathlib import Path
import tempfile
import unittest

from engine import Controller, Journal, geometry, identity
from settings import Settings, ratios
from test_engine import FakeHypr, MONITOR, window


class DisabledColumnTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.hypr = FakeHypr()
        self.settings = Settings(self.path / "settings.json")
        self.now = 10
        self.c = Controller(self.hypr, Journal(self.path / "journal.json"),
                            lambda: self.now, self.settings)

    def tick(self):
        self.now += 2
        self.c.reconcile()

    def test_all_one_and_two_column_combinations_fill_available_width(self):
        for values in ([0, 50, 50], [50, 0, 50], [50, 50, 0],
                       [100, 0, 0], [0, 100, 0], [0, 0, 100], [20.5, 0, 79.5]):
            with self.subTest(values=values):
                rectangles = geometry(MONITOR, [10]*4, [5]*4, 1, values)
                expected = [s for s, p in zip(("left", "center", "right"), values) if p]
                self.assertEqual(list(rectangles), expected)
                boxes = list(rectangles.values())
                self.assertEqual(boxes[0][0], 11)
                self.assertEqual(boxes[-1][0] + boxes[-1][2], 3429)
                for a, b in zip(boxes, boxes[1:]):
                    self.assertEqual(b[0] - a[0] - a[2], 12)
                self.assertTrue(all(r[2] > 0 for r in boxes))

    def test_scaled_two_columns_have_no_phantom_gap(self):
        monitor = dict(MONITOR, scale=1.25, x=-2752, reserved=[12, 32, 18, 48])
        rectangles = geometry(monitor, [8, 9, 10, 11], [2, 3, 4, 5], 2, [50, 0, 50])
        left, right = rectangles.values()
        self.assertEqual(right[0] - left[0] - left[2], 12)
        self.assertEqual(right[0] + right[2] + 2 + 9 + 18, 0)

    def test_new_windows_skip_disabled_columns_and_stack(self):
        self.settings.update(1, ratios=[0, 60, 40])
        self.hypr.clients = [window(n) for n in range(1, 6)]
        self.c.activate()
        self.tick()
        self.tick()
        self.assertEqual([r["slot"] for r in self.c.records.values()],
                         ["center", "right", "center", "right", "center"])
        self.assertEqual(self.c.workspaces, {1})
        self.assertTrue(all(c["floating"] for c in self.hypr.clients))
        self.assertFalse(any(call[0] == "move" for call in self.hypr.calls))

    def test_live_disable_and_reenable_keeps_every_window(self):
        self.hypr.clients = [window(n) for n in range(1, 7)]
        self.c.activate()
        self.tick()
        for values in ([50, 0, 50], [0, 100, 0], [30, 40, 30]):
            self.c.command({"command": "ratios", "value": values})
            self.tick()
            self.tick()
            self.assertEqual(len(self.c.records), 6)
            self.assertTrue(all(r["slot"] in self.c.active_slots(1) for r in self.c.records.values()))
            self.assertFalse(self.c.error)
            self.assertTrue(all(c["floating"] for c in self.hypr.clients))
            self.assertTrue(all(c["size"][0] > 0 and c["size"][1] > 0 for c in self.hypr.clients))
        self.hypr.clients.append(window(7))
        self.tick()
        self.assertEqual(self.c.records[identity(self.hypr.clients[-1])]["slot"], "left")

    def test_disable_on_hidden_workspace_reassigns_before_return(self):
        self.hypr.clients = [window(n) for n in range(1, 4)]
        self.c.activate()
        self.hypr.monitors[0]["activeWorkspace"] = {"id": 2, "name": "2"}
        self.settings.update(1, ratios=[50, 0, 50])
        self.tick()
        self.assertNotIn("center", [r["slot"] for r in self.c.records.values()])
        self.hypr.monitors[0]["activeWorkspace"] = {"id": 1, "name": "1"}
        self.tick()
        self.tick()
        self.assertEqual(len(self.c.records), 3)
        self.assertFalse(self.c.error)

    def test_optional_workspace_overflow_uses_enabled_capacity(self):
        self.settings.update(1, ratios=[50, 0, 50], overflow="workspace")
        self.hypr.clients = [window(n) for n in range(1, 6)]
        self.c.activate()
        records = list(self.c.records.values())
        self.assertEqual([r["workspace"] for r in records], [1, 1, 2, 2, 3])
        self.assertEqual([r["slot"] for r in records], ["left", "right", "left", "right", "left"])
        self.assertFalse(self.c.error)

    def test_edit_does_not_evict_existing_windows_with_workspace_overflow(self):
        self.settings.update(1, overflow="workspace")
        self.hypr.clients = [window(n) for n in range(1, 4)]
        self.c.activate()
        self.c.command({"command": "ratios", "value": [0, 0, 100]})
        self.tick()
        self.tick()
        self.assertEqual(len(self.c.records), 3)
        self.assertEqual(self.c.workspaces, {1})
        self.assertTrue(all(r["slot"] == "right" for r in self.c.records.values()))

    def test_hotkeys_skip_zero_center_and_stop_at_edges(self):
        self.settings.update(1, ratios=[50, 0, 50])
        self.hypr.clients = [window(1), window(2)]
        self.c.activate()
        c = self.hypr.clients[0]
        self.c.move_slot("r", c["address"], c["stableId"])
        self.assertEqual(self.c.records[identity(c)]["slot"], "right")
        self.c.move_slot("r", c["address"], c["stableId"])
        self.assertEqual(self.c.records[identity(c)]["slot"], "right")
        self.c.move_slot("l", c["address"], c["stableId"])
        self.assertEqual(self.c.records[identity(c)]["slot"], "left")
        self.c.command({"command": "ratios", "value": [0, 100, 0]})
        for direction in ("l", "r"):
            self.c.move_slot(direction, c["address"], c["stableId"])
        self.assertTrue(all(r["slot"] == "center" for r in self.c.records.values()))

    def test_zero_preset_survives_reload_but_all_zero_is_invalid(self):
        self.settings.save_preset(None, [0, 60, 40], 1)
        self.assertEqual(Settings(self.settings.path).presets[-1]["ratios"], [0, 60, 40])
        for values in ([0, 0, 0], [-5, 55, 50], [1, 0, 99]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                ratios(values)
