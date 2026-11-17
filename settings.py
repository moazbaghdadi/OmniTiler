"""Validated layout preferences, separate from the session recovery journal."""
import json
import math
import os
import uuid
from pathlib import Path


def ratios(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 3
            or any(isinstance(n, bool) or not isinstance(n, (int, float))
                   or not math.isfinite(n) or (n != 0 and n < 5) for n in value)
            or not math.isclose(sum(value), 100, abs_tol=0.001)):
        raise ValueError("Use 0 to disable a column, otherwise at least 5, totaling 100")
    return list(value)


class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.auto = False
        self.profiles = {}
        self.presets = [{"id": "balanced", "ratios": [30, 40, 30]},
                        {"id": "wide-center", "ratios": [25, 50, 25]}]
        if self.path and self.path.exists():
            data = json.loads(self.path.read_text())
            if type(data.get("auto", False)) is not bool:
                raise ValueError("auto must be true or false")
            self.auto = data.get("auto", False)
            if "presets" in data:
                self.presets = self.validate_presets(data["presets"])
            for workspace, profile in data.get("workspaces", {}).items():
                if not workspace.isdigit() or int(workspace) <= 0:
                    raise ValueError("Settings require positive numbered workspaces")
                self.profiles[workspace] = self.validate(profile)

    @staticmethod
    def validate(profile):
        result = {"ratios": ratios(profile.get("ratios", [30, 40, 30])),
                  "overflow": profile.get("overflow", "stack")}
        if result["overflow"] not in ("stack", "workspace"):
            raise ValueError("Overflow must be stack or workspace")
        return result

    def profile(self, workspace):
        return self.validate(self.profiles.get(str(workspace), {}))

    @staticmethod
    def validate_presets(values):
        if not isinstance(values, list) or not 1 <= len(values) <= 16:
            raise ValueError("Keep between 1 and 16 presets")
        result = []
        for item in values:
            key = item.get("id") if isinstance(item, dict) else None
            if (not isinstance(key, str) or not key or len(key) > 64
                    or not all(c.isascii() and (c.isalnum() or c in "-_") for c in key)
                    or any(p["id"] == key for p in result)):
                raise ValueError("Invalid or duplicate preset ID")
            result.append({"id": key, "ratios": ratios(item.get("ratios"))})
        return result

    def preset(self, key):
        return next((p for p in self.presets if p["id"] == key), None)

    def save_preset(self, key, percentages, workspace):
        """Save the shared preset and apply it to one workspace in one write."""
        value = ratios(percentages)
        if key is not None and self.preset(key) is None:
            raise ValueError("Preset no longer exists")
        key = key or uuid.uuid4().hex
        presets = [dict(p) for p in self.presets]
        previous = next((p for p in presets if p["id"] == key), None)
        if previous:
            previous["ratios"] = value
        else:
            presets.append({"id": key, "ratios": value})
        presets = self.validate_presets(presets)
        profiles = dict(self.profiles)
        profiles[str(workspace)] = dict(self.profile(workspace), ratios=value)
        self.save(profiles, self.auto, presets)
        self.profiles, self.presets = profiles, presets

    def update(self, workspace, **changes):
        profile = self.validate(dict(self.profile(workspace), **changes))
        profiles = dict(self.profiles, **{str(workspace): profile})
        self.save(profiles, self.auto)
        self.profiles = profiles

    def set_auto(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("auto must be true or false")
        self.save(self.profiles, enabled)
        self.auto = enabled

    def save(self, profiles, auto, presets=None):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            with temporary.open("w") as stream:
                json.dump({"auto": auto, "workspaces": profiles,
                           "presets": self.presets if presets is None else presets}, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
