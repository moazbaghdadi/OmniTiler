# OmniTiler — Ultrawide Window Tiler for Omarchy

This fork adds independent workspace layouts, configurable column widths, and
vertical stacking to [PixDevsApps/OmniTiler](https://github.com/PixDevsApps/OmniTiler).
The existing preview images show the upstream version.

## How it works

Enable tiling on a numbered workspace. Your focused window takes the center;
the next two take the left and right columns. Each workspace stays enabled
independently when you switch elsewhere or toggle another workspace.

The default proportions are **30 / 40 / 30**. Right-click the bar icon to open
**Column layouts**, with **30 / 40 / 30** and **25 / 50 / 25** presets. Click a
preview to apply it, choose **Edit**, or select **Add preset** to create another.
The editor previews your proportions, shows their total, and enables **Save &
apply** when enabled columns are at least 5% and they total 100%. Set **0%** to
disable a column: `0 / 60 / 40` or `50 / 0 / 50` gives two columns, and
`0 / 100 / 0` gives one full-width column. Disabled columns use no space or gaps;
window allocation and horizontal shortcuts skip them. Existing windows in a
disabled column stack into the remaining columns on the same workspace.
Re-enabling a column makes it available for new windows or keyboard moves.
Decimal percentages
use a dot. Enter saves; Escape cancels editing, then closes the panel.

Up to 16 presets are shared across workspaces. Applying or editing one affects
only the workspace shown in the panel; other workspaces keep their proportions.
Selecting a preset while tiling is off saves that workspace's preference for
its next activation. Custom percentages are also available through IPC below.
Ratios apply after subtracting borders, gaps, and reserved panel space.

Additional windows stay on the same workspace by default. Columns split
vertically, choosing the least populated column (center first on ties). Closing
a stacked window expands its remaining neighbors. No application is closed to
make room. Applications that cannot accept their assigned size eventually
return to normal Hyprland tiling, with an error in the tooltip.

Optional `workspace` overflow sends new excess windows to the next empty
numbered workspace on the same monitor. It inherits the source workspace's
preferences. Changing overflow mode affects future allocations; it does not
move existing windows back or redistribute existing stacks.

Middle-click enables automatic tiling as you visit normal numbered workspaces.
Turning a workspace off excludes it for this session until you explicitly
activate it or toggle automatic mode again. Turning automatic mode off keeps
already-managed workspaces enabled. Tiling starts off after login or shell/plugin
reload; saved preferences are reused on the next activation.

## Requirements

- Omarchy 4 with the Quickshell-based Omarchy shell (tested on 4.0.4).
- Hyprland with Lua dispatch and stable window IDs (tested on 0.56.2).
- Python 3.10+; only its standard library is used.
- The built-in Omarchy bar, which supplies the plugin's service access.

This is an **Omarchy shell plugin**, not a compiled Hyprland extension. It
does not edit Hyprland configuration or require root access.

## Install

The fork retains the upstream plugin ID. Use one installation only; the local
installer below replaces that ID's installed copy. The development changes must
be committed and pushed before installing them directly from the fork URL.

For a published version of the fork:

```sh
omarchy plugin add https://github.com/moazbaghdadi/OmniTiler --enable
omarchy plugin enable theboxer71.omnitiler --section center --after omarchy.clock
```

The second command places the icon immediately beside the centered clock.
Enabling the plugin loads its toggle; window tiling starts off until clicked.
For a Git-managed installation, update or remove with:

```sh
omarchy plugin update theboxer71.omnitiler
omarchy plugin remove theboxer71.omnitiler
```

### Local development installation

Clone the repository, then run the installer:

```sh
git clone https://github.com/moazbaghdadi/OmniTiler.git
cd OmniTiler
python3 manage.py install
```

This validates and copies the plugin into
`~/.config/omarchy/plugins/theboxer71.omnitiler/`, then enables its bar widget
immediately after the clock. It backs up `shell.json` under
`~/.local/state/omnitiler/backups/` and leaves the centered clock anchor intact.
Run the same command to update a local installation.

The installer restarts the Omarchy shell after enabling the plugin so updated
QML click handlers and IPC methods take effect. The bar briefly disappears and
tiling starts off. A plugin rescan alone can leave the old QML interface cached
while the new Python helper is already running. If an earlier installation has
working tiling but missing right/middle-click actions, run `omarchy restart shell`
once and enable tiling again.

Use either the Git-managed installation or the local development installer;
the latter installs a copy and is updated by rerunning `manage.py install`.

## Controls and IPC

- **Left click:** toggle only the current workspace.
- **Right click:** open or close the ratio preset settings panel.
- **Middle click:** toggle automatic activation of visited workspaces.
- **Hover:** see current ratios, overflow mode, managed workspaces, window counts,
  and any placement error.
- **IPC `deactivate`:** restore all managed workspaces and stop automatic activation.

### Omarchy keyboard shortcuts

| Shortcut | Behavior |
| --- | --- |
| **Super+Shift+Left / Right** | Move the focused window one column left/right; swap windows if occupied. |
| **Super+Left / Right** | Focus a neighboring window using Omarchy's normal navigation. |
| **Super+Shift+1…0** | Move a window to the chosen workspace. |
| **Super+Shift+Alt+1…0** | Move a window to a workspace without following it. |

With stacked columns, a move swaps with the first window in the adjacent column.
Moving between columns also adjusts the window to that column's width. Empty
columns accept moves, and outer edges do not wrap. The plugin only overrides
horizontal column movement; the Up/Down bindings are unchanged.
Moving an ordinary window into a managed workspace adopts an available slot;
moving it out returns it to normal tiling. Silent moves remain silent.

While active, OmniTiler temporarily replaces the two standard Omarchy
**Super+Shift+Left/Right** swap bindings with conditional handlers. Unmanaged
windows retain native swap behavior. Turning off or unloading the plugin
restores the standard bindings; a Hyprland reload reinstalls active handlers.
No Hyprland configuration files are edited. If either shortcut has a custom
description or nonstandard flags, activation reports the conflict instead of
overwriting it.

```sh
omarchy-shell omnitiler activate
omarchy-shell omnitiler deactivate
omarchy-shell omnitiler toggle
omarchy-shell omnitiler status
omarchy-shell omnitiler preset
omarchy-shell omnitiler ratios 25 50 25
omarchy-shell omnitiler ratios 20 45 35
omarchy-shell omnitiler overflow stack
omarchy-shell omnitiler overflow workspace
omarchy-shell omnitiler automatic true
omarchy-shell omnitiler automatic false
```

Commands acknowledge asynchronously; inspect `status` for the resulting state
and any validation error. Percentages must be 0 (disabled) or at least 5 and total 100.
`status` retains `active` (any managed workspace), `monitor` (last activation),
`workspaces`, `occupancy` (one address per occupied column for compatibility),
and `error`. New fields include `current_workspace`, `current_active`, `counts`
(window counts per column), `profile`, `profiles`, `auto`, and `auto_running`.

The IPC `preset` command cycles through all saved presets.

Preferences are written atomically to `$XDG_CONFIG_HOME/omnitiler/settings.json`
(default `~/.config/omnitiler/settings.json`). Ratios and overflow are keyed by
numbered workspace; the preset library and automatic-mode preference are global. They survive plugin
updates and removal. Active window assignments remain session-local. Use IPC to
change preferences while running; manual file edits are read on helper restart.

## Window handling

- Each ordinary toplevel window occupies a column or a row within it, including multiple windows
  from the same application.
- Already-floating windows, floating dialogs, hidden windows, pinned windows,
  window groups, and special workspaces are excluded. Ordinary non-floating
  windows are temporarily floated for exact positioning.
- Fullscreen is respected; exiting it returns a managed window to its slot.
- Moving a managed window to an unmanaged workspace releases it to normal
  tiling. Moving it into a vacant managed workspace adopts a vacant slot.
- Windows that repeatedly reject the requested geometry are released with an
  error in the tooltip. A minimum-size-constrained application may not fit a
  side column. Dragging/resizing managed windows is reconciled back to their
  assigned slots; turn OmniTiler off for free placement.
- Monitor scale, position, rotation, reserved space, and configured general
  gaps are included. Per-workspace gap overrides are not supported.
- Workspaces can be enabled on multiple monitors. Moving a whole managed
  workspace to another monitor recalculates its layout. Disconnecting a monitor
  releases workspaces still assigned to it; unaffected monitors keep their layouts.
- Inactive-workspace geometry is not used to reject windows. On return, the
  controller reconciles the visible workspace to its saved slot assignments.

## Lifecycle and recovery

The service owns one helper process, serialized by a session-local lock. The
helper journals only identities and slot assignments under
`$XDG_RUNTIME_DIR/omnitiler-*/`; no titles or application content are stored.
Before recovering a window it checks the compositor session, window address,
stable ID, and process ID. A small independent recovery watcher restores tiling
even when Quickshell forcibly terminates the helper during unload. The next
helper start also restores any remaining journal before accepting activation.
This runtime data does not carry over to a new login.

Removing the plugin's bar entry disables its service. To remove a local copy:

```sh
python3 manage.py remove
```

The removal script first restores managed windows, then removes only
OmniTiler's registration and directory. It does not restore an entire old
shell configuration over newer settings.

## Development

Node.js is needed only for the tooltip JavaScript test.

```sh
python3 -m unittest discover -s tests -v
omarchy plugin validate .
mkdir -p /tmp/omnitiler-qml-imports
ln -sfn /usr/share/omarchy/shell /tmp/omnitiler-qml-imports/qs
/usr/lib/qt6/bin/qmllint -I /tmp/omnitiler-qml-imports Service.qml BarWidget.qml SettingsPanel.qml SettingsContent.qml RatioPreview.qml
```

`engine.py` separates the geometry/allocation controller from the compositor
adapter. The QML service communicates with the helper using newline-delimited
JSON on stdin/stdout. Standard input EOF or SIGTERM requests cleanup. The
helper listens to Hyprland's event socket and reconciles once per second while
active, including recovery from missed events. It performs no network calls.

Historical upstream live checks (not yet adapted to default stacking; see
[verification](docs/VERIFICATION.md)). They temporarily open/close demonstration
windows and some also change shell state, so do not use them as the fork's
acceptance suite:

```sh
python3 tests/live_smoke.py --run
python3 tests/live_lifecycle.py --run
python3 tests/live_hotkeys.py --run
```

The lifecycle check also temporarily switches themes, tests helper recovery,
and removes/reinstalls the local plugin. It restores the original theme,
background, workspace, and focus when finished. See the
[light-theme preview](docs/preview-light.png) for the empty-side-column state.
The keyboard check uses a disposable virtual input device and requires
existing write access to `/dev/uinput`; it does not change device permissions.

See [marketplace material](docs/MARKETPLACE.md), [verification](docs/VERIFICATION.md),
and [changelog](CHANGELOG.md). Licensed under MIT.
