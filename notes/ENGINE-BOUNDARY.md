# Engine and persistence boundaries

## Connected client boundary

Ordinary launch connects to the selected AHP 0.9 WebSocket host. A bundled Node
sidecar uses the official AHP SDK/reducers; Python adapts bounded presentation data
to the existing Ratatui renderer and owns local drafts/outbox. No connected module
imports Core/Foundation/CLI or reads native session files. Agent implementations
and execution ownership belong to the independently installed host and ACP agent.
Catalogs use standard opaque cursors scoped to a connection; selected sessions/chats
alone are subscribed. Explicit historical backfill uses fetchTurns. Derived protocol
state stays in memory; a restarted client obtains fresh snapshots. Live reconnect
uses upstream replay/snapshot semantics and refetches ephemeral catalog information.
Neither path resends an uncertain command. Stable turn IDs reconcile durable local
intent against host receipts or observed accepted turns. Unknown input remains
inspectable, never offered as an unsafe automatic or fresh-identity retry.
Private editor state stays on client disk. Disconnect/exit only detaches. Missing
queue/steer/takeover/device/configuration capabilities explicitly refuse. Standard
cancel is not force termination. Node 22 and the packaged native renderer are runtime
requirements; source builds bundle SDK code, so ordinary launch needs no npm install.

