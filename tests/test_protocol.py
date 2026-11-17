"""Exercise the helper's command stream and cleanup without touching Hyprland."""
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import engine
from test_engine import FakeHypr, window


class ProtocolTests(unittest.TestCase):
    def test_command_stream_validation_and_eof_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeHypr([window(1)])
            backend.directory = Path(directory) / "hypr/session"
            output = io.StringIO()
            commands = '\n'.join([
                '[]', '{"command":"activate"}',
                '{"command":"ratios","value":[25,50,25],"request_id":10}',
                '{"command":"ratios","value":[1,2,3],"request_id":11}',
                '{"command":"status"}',
            ]) + '\n'
            with patch.object(engine, "Hyprland", return_value=backend), \
                    patch.object(engine, "event_reader"), \
                    patch.object(engine.subprocess, "Popen"), \
                    patch.object(engine.signal, "signal"), \
                    patch.dict(os.environ, {"XDG_RUNTIME_DIR": directory, "XDG_CONFIG_HOME": directory}), \
                    patch.object(engine.sys, "stdin", io.StringIO(commands)), \
                    patch.object(engine.sys, "stdout", output):
                engine.main()
            states = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertTrue(any(s["current_active"] for s in states))
            self.assertTrue(any("Invalid JSON" in s["error"] for s in states))
            self.assertEqual(states[-1]["profile"]["ratios"], [25, 50, 25])
            self.assertIn("totaling 100", states[-1]["error"])
            replies = {s["reply"]["id"]: s["reply"] for s in states if "reply" in s}
            self.assertTrue(replies[10]["ok"])
            self.assertFalse(replies[11]["ok"])
            self.assertFalse(backend.clients[0]["floating"])
            self.assertFalse(backend.hotkeys)

    def test_tooltip_markup_is_escaped(self):
        root = Path(__file__).resolve().parents[1]
        # Run the same JS helper imported by QML, with no shell interpolation.
        subprocess.run(["node", "-e", """
            const fs = require('node:fs');
            const vm = require('node:vm');
            const assert = require('node:assert/strict');
            const scope = {};
            vm.runInNewContext(fs.readFileSync('TextSafety.js', 'utf8'), scope);
            assert.equal(scope.escapeMarkup('<img src="https://invalid.test/x">&'),
                '&lt;img src="https://invalid.test/x"&gt;&amp;');
            assert.equal(scope.escapeMarkup('30% | 40% | 30%'), '30% | 40% | 30%');
        """], cwd=root, check=True, timeout=10)
