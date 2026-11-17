"""Validated layout preferences, separate from the session recovery journal."""
import json
import math
import os
from pathlib import Path


def ratios(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 3
            or any(isinstance(n, bool) or not isinstance(n, (int, float))
                   or not math.isfinite(n) or n < 5 for n in value)
            or not math.isclose(sum(value), 100, abs_tol=0.001)):
        raise ValueError("Provide three percentages of at least 5, totaling 100")
    return list(value)


class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.auto = False
        self.profiles = {}
        if self.path and self.path.exists():
            data = json.loads(self.path.read_text())
            if type(data.get("auto", False)) is not bool:
                raise ValueError("auto must be true or false")
            self.auto = data.get("auto", False)
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

    def save(self, profiles, auto):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            with temporary.open("w") as stream:
                json.dump({"auto": auto, "workspaces": profiles}, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
