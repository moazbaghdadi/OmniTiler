# Changelog

## 0.3.1 — fork, unreleased

- Keep workspaces enabled when their monitor sleeps or disconnects: suspend
  them and resume once the monitor returns. Previously, HDMI monitors that
  hotplug-disconnect while asleep came back with tiling turned off.
- Remember enabled workspaces in `settings.json` and re-tile them after login,
  shell/plugin reload, or reinstall. Turning a workspace off forgets it; IPC
  `deactivate` forgets all of them.
- Fix a Hyprland crash when the screen locks and every display powers off:
  OmniTiler no longer changes a window's floating state unless the window is
  on a live monitor, checked inside the compositor in the same call. With no
  outputs it pauses and keeps its layouts; restores that could not run wait in
  the recovery journal until a monitor returns, instead of failing startup.
- Allow 0% to disable a column, including two-column and single-column layouts.
- Remove disabled columns from geometry, gaps, allocation, overflow capacity,
  keyboard navigation, and the settings preview.
- Reassign existing windows from disabled columns to the remaining columns
  without moving them to another workspace. Re-enabling a column makes it
  available for new windows or keyboard moves; existing assignments stay put.
- Add coverage for all one/two-column combinations, live changes, inactive
  workspaces, scaling, stacking, overflow, shortcuts, and preset persistence.

## 0.3.0 — fork, unreleased

- Open a native settings panel on right click, with visual ratio previews,
  preset selection, and Add/Edit forms with live total validation.
- Save up to 16 shared presets, including edits to the initial 30/40/30 and
  25/50/25 presets. Apply changes only to the workspace captured when opened.
- Persist preset edits and the selected workspace's ratios atomically. Existing
  settings files gain default presets without losing workspace preferences.
- Keep failed saves in the editor with a visible error; acknowledge commands
  individually so the panel does not claim success before a disk write completes.
- Add headless Quickshell tests for mouse actions, Enter/Escape, validation,
  and failed saves, plus preset storage and workspace-isolation coverage.

## 0.2.0 — fork, unreleased

- Restart the shell after local installation to replace cached QML click handlers
  and IPC methods; a rescan alone could leave right/middle click nonfunctional.
- Keep independent layouts active across workspaces and monitors.
- Change left click to toggle only the current workspace; IPC `deactivate`
  still restores every managed workspace for shutdown and recovery.
- Stack additional windows vertically in columns by default. Retain next-empty
  workspace overflow as an explicit per-workspace option.
- Persist per-workspace column ratios and overflow preferences outside the
  plugin directory. Add right-click ratio presets and IPC custom percentages.
- Add middle-click automatic activation on visited numbered workspaces, with
  session-local opt-outs for workspaces disabled manually.
- Stop checking geometry on inactive workspaces; allow five placement retries
  for slow or size-constrained clients, with a visible error on fallback.
- Add workspace-aware status, column counts, English translation catalog,
  tooltip markup escaping, and regression coverage for the helper protocol.
- Preserve the upstream plugin ID for replacement installs; do not run the
  upstream and fork concurrently. Existing preview images show upstream 0.1.

## 0.1.1 — 2026-09-16

- Support Omarchy's Super+Shift+Left/Right for moving and swapping columns.
- Preserve slot assignments after keyboard movement and resize each swapped window.
- Adopt ordinary windows moved into managed workspaces with workspace shortcuts.
- Restore native shortcuts on disable/unload and reinstall handlers after reload.
- Add real keyboard integration checks, including focus and silent workspace moves.
- Add marketplace showcase artwork, retaining real dark/light desktop screenshots.
- Document GitHub installation, updates, removal, and marketplace listing metadata.

## 0.1.0 — 2026-09-16

- Fixed center-first 30/40/30 ultrawide window layout.
- Automatic next-empty-workspace overflow with focus following new windows.
- Theme-aware center-section bar toggle and occupancy tooltip.
- Session recovery, identity-checked cleanup, and dependency-free Python helper.
- Local installer/remover, automated tests, and marketplace preparation.
