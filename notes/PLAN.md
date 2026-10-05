# Work derived from current direction

Authority: [VISION](../docs/VISION.md) and the referenced DRAFT contracts.
Desired behavior is distinct from current [acceptance](ACCEPTANCE.md).

| Item | Source promises | Work | Observable completion / falsifier | State |
|---|---|---|---|---|
| AHP-01 | composition.v1:1, continuity.v1:2, session.v1:2 | Independent AHP client, durable local intent, paged selected resources | Official reducer plus independent host and installed Ratatui PTYs; no command replay | Implemented; source qualification recorded in ACCEPTANCE |
| STREAM-01 | performance.v1:5, presentation.v1:3 | Append active text without copying growing responses through local IPC | Long stream preserves exact bytes and responsive draft input; IPC instrumentation | Implemented; bounded append instrumentation and real PTY regression |
| PARITY-01 | interaction.v1:1, session.v1:6 | Bind remaining optional host controls through negotiated capabilities | Same supported action for person and agent; explicit unsupported inventory | Remaining surfaces listed in README; no private runtime bypass |
| PEERS-01 | ecosystem.v1:6 | Independently qualify other AHP hosts and ACP-backed implementations | Separate source, handshake, tool/approval, model and real-account receipts | Independent host fixture passes; external account qualification remains |

| FLAGS-01 | composition.v1:1, session.v1:6 | F21.04 configured managed launch choices | Passive options resolve exact bundle revision; first installed native model audit matches explicit selection; resumed/unsupported overrides refuse | Implemented; acceptance tracked in CONNECTED-PARITY |
| REVIEW-01 | continuity.v1:2, presentation.v1:7 | Recovery and managed allocation reviews | Exact source/revision confirmation, durable original receipt, stale target refuses, source history preserved | Implemented; acceptance tracked in CONNECTED-PARITY |
| CATALOG-01 | composition.v1:1, interaction.v1:1 | Negotiated workspace/root-session discovery | 50-row host-filtered pages; cursor binds query/workspace/connection; no dormant runtime | Implemented; acceptance tracked in CONNECTED-PARITY |

| WHEEL-01 | composition.v1:1, ecosystem.v1:6 | Reproducible native wheel build and installed client | Compiler deployment floor and isolated host proc-macro artifacts; installed helper/native isolation and actual connected PTYs | Implemented; causal evidence in WHEEL-BUILD |

| CONFIG-01 | session.v1:6, ecosystem.v1:2, continuity.v1:2 | Standard connected model/settings selection and truthful optional controls | Advertised mutable schema choices, readback confirmation, refusal/unknown distinction, local draft preservation and receipt-only inspection | Implemented; standard installed host and actual terminal picker/refusal qualified; fresh native schema boundary reported separately |
| MESSAGE-01 | interaction.v1:3, continuity.v1:4, ecosystem.v1:2 | Private canonical quotes and authenticated shared reactions | Reload and selection preserve drafts; no RPC on quote selection; bounded metadata reads, exact reaction receipts, missing refs and unknown outcomes never replay | Implemented; exact installed public-host/native and PTY evidence in MESSAGE-PARITY; selected metadata watch qualified in MESSAGE-WATCH-01 |

| QUOTE-RECOVERY-01 | interaction.v1:3, continuity.v1:2, continuity.v1:4 | Original frozen quoted submission survives native refusal after host admission | Stale digest/native unknown execution retains exact private text/quote/command through reload, read-only inspection and newer draft/quote without any replay | Implemented; stale-digest native refusal, exact original reload and installed terminal inspection/copy passed; independent review required |

| MESSAGE-WATCH-01 | continuity.v1:3, continuity.v1:4, ecosystem.v1:2 | Selected shared reaction updates via public resource watches | Other-client changes update current projection; stale scope/revision refuses, one coalesced read, detach/reconnect never repeat effects | Implemented; other-client live updates, reconnect and exact original uncertainty tested in installed public-host/native PTYs |

Selection watch repair: retain at most one latest validated metadata packet for
an in-flight selected scope and connection generation. Commit it only after the
matching selection snapshot; discard on cancellation, replacement or reconnect.
Serialize selections so a late snapshot cannot replace a newer view. This keeps
public selected-resource projection and private unknown receipts independent.

Pending selection reconnect: a validated watch packet explicitly stamped with
the current transport generation may replace the pending selection's old-generation
buffer. Keep its same selection token/scope, discard the old packet, and compare
revisions only within that generation. Reject old-generation packets and keep
cancellation/replacement cleanup. No additional read or input replay is needed.

| RELEASE-01 | composition.v1:1, ecosystem.v1:6, continuity.v1:2 | Versioned qualified wheel manifest and supported-platform CI artifacts | Exact new-repository source/version, AHP/runtime/platform/bytes/hash bindings, independent installed/isolation/PTY/privacy receipts; failed or unqualified targets absent; root alone publishes after review | Proposed; release manifest validation and safe evidence packaging under qualification |

RELEASE-01 review repair: refuse nonregular/symlink input through no-follow,
nonblocking descriptors before reading. Bound JSON at MAX_BYTES+1, stream wheel
hash/copy within declared bytes, and reject descriptor/path identity or content
changes. Preserve f6 evidence; requalify a separate successor before adoption.

Unknown-delivery fixture synchronization (continuity.v1:2, continuity.v1:4):
host admission does not prove the original provider prompt has started. Before
injecting an unknown receipt, wait within the existing ten-second bound for a
complete original audit record and validate its exact command identity and text
against the private intent journal. Missing, malformed or wrong records fail;
retain read-only retry, unchanged provider audit and unknown-status assertions.
This changes test ordering only; earlier qualified source identities remain intact.

PTY observer receipt repair (continuity.v1:2): concurrent probe cleanup must retain
every resource identity/status in its shared test receipt. Serialize thread updates
and atomically replace the receipt in its own directory so readers see complete
JSON. Malformed existing receipts must still fail without replacement. Qualify a
new exact source; retain the earlier passing source and failed cleanup receipts.

Simulated renderer observer repair (presentation.v1:3, continuity.v1:2): a
fixed settling delay cannot prove complete geometry, and a coalesced PTY read
may omit an intermediate busy projection. Bound the geometry wait by its exact
composer rows/text. Bind explicit Tab submission to its new user/response text,
complete composer/actions and Ready footer observed after input. Keep general
wait_idle transition requirements and all geometry/teardown assertions unchanged.
Controlled fragmented/coalesced mechanisms are separate from actual Mac evidence.

Managed runtime qualification (ecosystem.v1:6, composition.v1:1): preserve the
qualified wheel/source evidence and supplement it with exact checksum-bound
managed Python/Node archive identities, Node executable digests, and actual
installed PTYs on the already-supported Intel Linux/macOS runners. Use reviewed
same-repository host inputs and previously sealed wheel artifacts; no client
behavior change, native rebuild, user credentials, publication, or feed binding.
Keep managed-runtime acceptance distinct from earlier system/runner-cache
qualification and from account, physical-device, older-OS, or live acceptance.

The supplement uses the reviewed standalone Root install client's exported safe
extraction API as a provenance-bound test peer. Bootstrap reads only the exact
regular Node member from its verified archive. Root's bounded no-link-traversal
policy then unpacks both archives; escaping links and special files still refuse.
The earlier Python 3.10 tarfile refusal and earlier Mac success remain separate.

Installed model-picker observer (continuity.v1:2): local composer visibility and
a fixed 300 ms pause do not prove retained draft state after its 250 ms debounce
and IPC. Await the complete local text and exact saved draft under its original
session, within the existing displayed timeout and live-process check. Retain
exact text, confirmed/refused settings, two changes and zero prompts assertions.
The supplemental observer commit is separate from the unchanged sealed wheel's
731 source; historical 4-pass/1-failure evidence and final teardown state remain.

The persistence observer controls run with the exact verified managed Python after Root extraction. Linux runner bootstrap Python 3.10 lacks asyncio.timeout; this interpreter placement correction leaves observer assertions and product bytes unchanged.

| REUSE-01 | composition.v1:2, continuity.v1:6, continuity.v1:7 | User-approved on-demand agents and automatic host-managed bounded reuse | No terminal pool controls or navigation-triggered preparation; host preserves history/running work | Optional session.warm on selection removed; focused donor-backed selection/Send regression passed; full installed qualification pending |

REUSE-01 source inventory: connected launch flags, standard-schema settings, native menus/navigation, and the packaged SDK sidecar contain no legacy Ready conversations or warm-pool setting. Selection previously scheduled an optional session.warm action. Remove only that advisory preparation; keep snapshot/subscription, private draft persistence, cancellation and execution actions unchanged. Host owners remove legacy schema fields and own reuse bounds. After allocation clearance, qualify an independent host advertising session.warm: open/switch/reconnect must issue no preparation command, explicit Send must still work, and drafts, retained history and running work must survive detach and selection. Existing sealed wheel receipts describe their original bytes.

REUSE-01 narrow verification: the existing independent public-host/ACP fixture advertises the legacy warm action through a controlled transport capability hook and records every client command. Baseline 537eb8c fails the no-warm assertion. The candidate opens and switches a saved chat without preparation or extra prompts, preserves its private draft and saved response, and two explicit prompts produce exactly two provider records/responses. This verifies the client command boundary; host reuse policy, reconnect, active-work preservation and installed renderer acceptance remain separate. Existing donor runtimes were reused; fixture allocations stayed below one MiB.

| QUEUE-01 | session.v1:2, session.v1:6, continuity.v1:2, ecosystem.v1:2 | Advertised standard connected follow-ups | Standard pending set/remove; two clients, held rearm, exact IDs and original uncertainty; no native calls/local scheduler | Implemented; 12 public-host cases, 4 updated native PTYs, 2 basic PTYs and no-warm regression pass on Mac ARM |

Queue seam inventory: Web 79681952 uses standard AHP pendingMessageSet/remove/reorder for queued inputs and has no steer handler/UI; exact Host 473e7829 (source 72c975f5) provides shared bounded queue, per-item held metadata and explicit upsert rearm. No global pause/run operation is advertised. TUI consumes official reducer queue state and maps Queue/edit/remove/per-entry Resume with existing original intent journal. No local queue, new protocol or native session access. Legacy local global controls must not appear in connected menus. Independent protocol review establishes standard chat-scoped steering: SDK 0.9 pending messages have no expected-turn field; idle steering waits for this chat’s next active turn. Adopt truthful current/next-turn UI and immutable selected-chat routing, not a new precondition extension. Host/native generation anchoring remains authoritative. Queue quoted attachments remain unsupported until frozen-reference parity is separately mapped; refusal preserves draft/quote.

Standard steering authority: https://microsoft.github.io/agent-host-protocol/specification/chat-channel.html#steering-messages . Host admission, pending removal and native application remain distinct; original IDs and intent survive unknown results without replay.

QUEUE-01 verification boundary: twelve pending-input cases use sealed public Host npm SHA-256 0137e4e5042a56e3593f45b1648418f025a3c37d37ac87269ebb7679e8d20d0a and an independent ACP peer. Shared edit/remove/drain, cancellation-held same-ID rearm, uncertain acknowledgement/exception retention, reconnect without replay, idle/current steering, withdrawal, native capability refusal, exact applied/held/unknown typed receipts, private quote preservation and shared pending projection pass. Four actual updated Ratatui PTYs qualify shared Queue/edit/cancel-held/same-ID Resume, private steering before Enter followed by exact applied receipt, and agent queue/steer through the real renderer revision gate while a second view preserves its draft. Two basic PTYs at 120x40 and 40x20 qualify send/approval/private-draft/exit, and the no-warm regression passes: nineteen cases, zero skips. The Mac ARM component was built offline from 6cc295862c765261e3c5ed74cc01bb19bc89a15b using the existing component cache; native SHA-256 05eb430e3d971384ad31792b1caf7b852670a68cdcba43f4b78162f6210a96ef. Later test-observer/documentation edits leave all build/runtime inputs unchanged. Initial source-only and older-binary regressions are separate historical evidence; they do not qualify the new routes. No wheel, multi-platform release, full composition, live application, real provider account or physical terminal acceptance was attempted. Independent review remains required before Root merges.
