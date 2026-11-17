# Changelog

## 0.2.0 — fork, unreleased

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
