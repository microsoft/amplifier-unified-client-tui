# Acceptance evidence

The connected source baseline is amplifier-unified-client-tui commit
41696a004c1b3e6e846020bbe99ec93ce0b28a25 in the retained local historical checkout.
That baseline passed 106 Python tests, one intentionally absent private-archive
skip, 79 Rust tests, a fresh independent wheel installation and four installed
actual terminal PTYs. The observer measures terminal cells, not physical-device paint.

A 128-chunk response retained 131,092 response bytes; the protocol bridge emitted
310,318 bytes and the renderer received 323,400 bytes. Exact content, reconnect and
local typing stayed covered. These observations demonstrate bounded append traffic,
not a comparative CPU/RSS or production Spark latency claim.

This fresh repository exports identical production source/build inputs. It removes
obsolete standalone/HTTP tests and unused engine-preparation fixtures; selected
current renderer tests keep their exact bodies. The former engine-policy capture
test is outside this client boundary. Export checks verify portable document links,
current test collection and lint. Packaging alone does not re-prove changed behavior.

No production service, Spark state, paid model, provider account, physical terminal,
external clipboard or other-platform release was used to establish these results.
Use scripts/qualify_current.py to repeat full source/build/install/PTY qualification
against an independently built host artifact. No publication is implied.
