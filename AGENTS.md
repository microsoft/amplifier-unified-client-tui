# Amplifier Unified Client TUI

Read docs/VISION.md, contracts/, notes/CONVERGE.md, notes/PLAN.md,
notes/ENGINE-BOUNDARY.md and SMOKE_TESTS.md before changing behavior.
This repository owns only the native Ratatui AHP client and its local presentation
bridge. Never import Core, Foundation, native agent or host internals. Use the
published AHP SDK/reducers and independently installed public host entrypoints.
Drafts, editing, selection and unknown-effect journals remain local. Never replay
uncertain commands or silently drop required protocol state to meet a limit.
Native/session execution, discovery and history writing belong to host/ACP owners.
Amend desired direction before implementation; cite contract promises in PLAN.
Contracts are DRAFT; green syntax/tests do not imply ratification or formal verdicts.
Run scripts/qualify_current.py with owned independent host artifacts. Preserve real
PTY renderer tests, source/build/installed evidence and explicit provider/device limits.
Keep secrets, personal histories, private archives and machine paths out of Git.
Do not modify or publish the older amplifier-app-tui repository from this checkout.

This codebase is yours: what it's for and how it's built are your call, and you'll keep building on it.

## Ecosystem maps

Keep this repository's README and product-page maps aligned with the
[Constellation map guide](https://github.com/microsoft/amplifier-constellation/blob/main/docs/ecosystem-maps.md)
and its canonical registry; start with this repository's
`docs/ecosystem-map.json`. When creating, renaming, splitting, retiring, or
changing a role, interface, parent, or dependency, inspect incoming and outgoing
relationships and update every affected parent/consumer map and link, including
the centralized product pages. Regenerate from source data and synchronize local
records/images rather than hand-editing generated images. Describe actual
boundaries and optional choices; a role highlight is not a compatibility claim.
Documentation work does not authorize deployment or resume paused product work.
