"""Installer ordering without touching the user's shell or configuration."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import manage


class InstallTests(unittest.TestCase):
    def test_replacement_restarts_shell_after_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, config = root / "source", root / "config"
            target = config / "plugins" / manage.ID
            source.mkdir()
            target.mkdir(parents=True)
            manifest = json.dumps({"id": manage.ID})
            (source / "manifest.json").write_text(manifest)
            (target / "manifest.json").write_text(manifest)
            (source / "Service.qml").write_text("new service")
            (target / "Service.qml").write_text("old service")
            (config / "shell.json").write_text(json.dumps({"bar": {"layout": {
                "center": [{"id": "omarchy.clock"}]}}}))
            actions = []

            def run(*args, **kwargs):
                actions.append(args)
                if args == ("omarchy", "restart", "shell"):
                    self.assertEqual((target / "Service.qml").read_text(), "new service")
                    self.assertEqual(kwargs["timeout"], 60)

            with patch.multiple(manage, SOURCE=source, CONFIG=config, TARGET=target), \
                    patch.object(manage, "run", side_effect=run), \
                    patch.object(manage, "backup"), \
                    patch.object(manage, "stop", side_effect=lambda: actions.append(("stop",))), \
                    contextlib.redirect_stdout(io.StringIO()):
                manage.install()
            self.assertLess(actions.index(("stop",)),
                            actions.index(("omarchy", "plugin", "disable", manage.ID)))
            self.assertEqual(actions[-2], ("omarchy", "plugin", "enable", manage.ID,
                                           "--section", "center", "--after", "omarchy.clock"))
            self.assertEqual(actions[-1], ("omarchy", "restart", "shell"))
